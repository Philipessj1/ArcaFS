from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from fastapi.responses import FileResponse as FastAPIFileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.file import File
from app.models.file_version import FileVersion
from app.models.user import User
from app.storage.local import save_file_locally
from app.storage.validation import validate_upload_file


# Core orchestration service to validate, persist physically, and register a user asset with version control
def upload_file(
    db: Session,
    upload_file: UploadFile,
    current_user: User,
) -> File:
    # Execute interceptor guards to validate mimetype depth and multi-part volumetric limits
    validate_upload_file(upload_file)

    # Persist the file stream to the local isolated storage disk using tenant scoping
    stored_filename, stored_path, size = save_file_locally(
        upload_file=upload_file,
        user_id=current_user.id
    )

    # Initialize the core database file record holding structural tracking metadata
    file_record = File(
        original_filename=upload_file.filename,
        stored_filename=stored_filename,
        stored_path=stored_path,
        content_type=upload_file.content_type,
        size=size,
        owner_id=current_user.id
    )

    # Enclose stateful write operations within a transaction block to preserve data integrity
    try:
        # Stage the file record instantiation to populate and generate the primary identity key
        db.add(file_record)
        db.flush()

        # Initialize the baseline historical version tracker linked to the newly generated file index
        initial_version = FileVersion(
            file_id=file_record.id,
            version_number=1,
            original_filename=file_record.original_filename,
            stored_filename=file_record.stored_filename,
            stored_path=file_record.stored_path,
            content_type=file_record.content_type,
            size=file_record.size
        )

        # Stage the history entry and atomitically commit both record states to the database
        db.add(initial_version)
        db.commit()
        db.refresh(file_record)

        # Return the synchronized core file record model object
        return file_record

    except Exception:
        # Roll back the active unit of work transaction to prevent orphaned or partial entity records
        db.rollback()

        # Instantiate a Path object pointing to the orphaned disk binary asset
        saved_path = Path(stored_path)

        # Unlink and purge the dangling binary from disk storage if it was partially written
        if saved_path.exists():
            saved_path.unlink()
        
        # Rethrow the original exception to upstream interceptors
        raise

# Service function to list all files owned by the current user
def list_user_files(
    db: Session,
    current_user: User,
) -> list[File]:

    # Execute a query to retrieve all file records associated with the current user's ID, ordered by creation timestamp in descending order
    return list(
        db.scalars(
            select(File)
            .where(File.owner_id == current_user.id)
            .order_by(File.created_at.desc())
        )
    )

# Service function to retrieve a specific file record by its ID, ensuring it belongs to the current user
def get_user_file_or_404(
    db: Session,
    file_id: int,
    current_user: User,
) -> File:

    # Execute a query to retrieve the file record by its ID and ensure it belongs to the current user
    file_record = db.scalar(
        select(File)
        .where(File.id == file_id, File.owner_id == current_user.id)
    )

    # If the file record is not found, raise an HTTP 404 Not Found exception
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # Return the retrieved file record
    return file_record

def download_user_file(
    db: Session,
    file_id: int,
    current_user: User,
) -> FastAPIFileResponse:

    # Retrieve the file record for the specified file ID, ensuring it belongs to the current user
    file_record = get_user_file_or_404(
        db, 
        file_id, 
        current_user,
    )

    # Resolve the physical path of the stored file on disk using the stored_path attribute from the file record
    file_path = Path(file_record.stored_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on storage"
        )

    # Return a FastAPI FileResponse object to facilitate file download, using the stored path and original filename
    return FastAPIFileResponse(
        path=file_path,
        filename=file_record.original_filename,
        media_type=file_record.content_type
    )

# Service function to delete a specific file record by its ID, ensuring it belongs to the current user and removing the associated physical file from disk
def delete_user_file(
    db: Session,
    file_id: int,
    current_user: User,
) -> None:

    # Retrieve the file record for the specified file ID, ensuring it belongs to the current user
    file_record = get_user_file_or_404(
        db=db, 
        file_id=file_id, 
        current_user=current_user,
    )
    
    file_path = Path(file_record.stored_path)

    # Enclose the deletion of the database record and the physical file in a try-except block to handle potential errors and ensure transactional integrity
    try:
        db.delete(file_record)
        db.commit()

        if file_path.exists():
            file_path.unlink()
    
    except Exception:
        db.rollback()
        raise