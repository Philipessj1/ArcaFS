from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from fastapi.responses import FileResponse as FastAPIFileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.file import File
from app.models.file_version import FileVersion
from app.models.user import User
from app.services.file_service import get_user_file_or_404
from app.storage.provider import get_storage_backend
from app.storage.validation import validate_upload_file

# Service function to create a new version of an existing file, ensuring it belongs to the current user and validating the uploaded file
def list_file_versions(
    db: Session,
    file_id: int,
    current_user: User,
) -> list[FileVersion]:
    # Retrieve the file record for the specified file ID, ensuring it belongs to the current user
    file_record = get_user_file_or_404(
        db=db, 
        file_id=file_id, 
        current_user=current_user,
    )

    # Query the database for all FileVersion records associated with the specified file ID, ordered by version number in descending order
    return list(
        db.scalars(
            select(FileVersion)
            .where(FileVersion.file_id == file_record.id)
            .order_by(FileVersion.version_number.desc())
        )
    )

# Service function to create a new version of an existing file, ensuring it belongs to the current user and validating the uploaded file
def create_new_file_version(
    db: Session,
    file_id: int,
    current_user: User,
    uploaded_file: UploadFile,
) -> FileVersion:
    # Validate the uploaded file to ensure it meets the required criteria (e.g., size, type)
    validate_upload_file(uploaded_file)

    # Retrieve the file record for the specified file ID, ensuring it belongs to the current user
    file_record = get_user_file_or_404(
        db=db, 
        file_id=file_id, 
        current_user=current_user,
    )

    storage = get_storage_backend()

    # Save the uploaded file to local storage and obtain the stored filename, path, and size
    stored_filename, stored_path, size = storage.save_file(
        upload_file=uploaded_file,
        user_id=current_user.id,
    )

    # Copy the uploaded file to a local storage location for versioning purposes
    try:
        latest_version_number = db.scalar(
            select(func.max(FileVersion.version_number))
            .where(FileVersion.file_id == file_record.id)
        )

        next_version_number = (latest_version_number or 0) + 1

        version = FileVersion(
            file_id=file_record.id,
            version_number=next_version_number,
            original_filename=uploaded_file.filename,
            stored_filename=stored_filename,
            stored_path=stored_path,
            content_type=uploaded_file.content_type,
            size=size,
        )

        file_record.original_filename = uploaded_file.filename
        file_record.stored_filename = stored_filename
        file_record.stored_path = stored_path
        file_record.content_type = uploaded_file.content_type
        file_record.size = size


        # Add the new FileVersion record to the database session and commit the transaction
        db.add(version)
        db.commit()
        db.refresh(version)

        return version
    # If any exception occurs during the file version creation process, roll back the database transaction and delete the saved file from local storage to maintain data integrity
    except Exception:
        db.rollback()

        storage.delete_file(stored_path)
        
        raise

# Service function to retrieve a specific file version by its file ID and version number, ensuring it belongs to the current user
def get_file_version_or_404(
    db: Session,
    file_id: int,
    version_number: int,
    current_user: User,
) -> FileVersion:
    # Query the database for the specific FileVersion record by its file ID and version number, ensuring it belongs to the current user
    version = db.scalar(
        select(FileVersion)
        .join(File)
        .where(
           File.id == file_id,
           File.owner_id == current_user.id,
           FileVersion.file_id == file_id,
           FileVersion.version_number == version_number,
        )
    )

    # If the version record is not found, raise an HTTP 404 Not Found exception
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File version not found"
        )

    return version

# Service function to download a specific file version by its file ID and version number, ensuring it belongs to the current user
def download_file_version(
    db: Session,
    file_id: int,
    version_number: int,
    current_user: User,
) -> FastAPIFileResponse:

    version = get_file_version_or_404(
        db=db,
        file_id=file_id,
        version_number=version_number,
        current_user=current_user,
    )

    file_path = Path(version.stored_path)

    storage = get_storage_backend()
    
    # If the file path does not exist, raise an HTTP 404 Not Found exception indicating that the file version is not found
    if not storage.exists(version.stored_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File version not found",
        )
    
    download_path = storage.download_to_temp_file(version.stored_path)

    return FastAPIFileResponse(
        path=download_path,
        filename=version.original_filename,
        media_type=version.content_type,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )

# Service function to restore a specific file version as the current version of the file, ensuring it belongs to the current user
def restore_file_version(
    db: Session,
    file_id: int,
    version_number: int,
    current_user: User,
) -> FileVersion:
    
    # Retrieve the file record for the specified file ID, ensuring it belongs to the current user
    file_record = get_user_file_or_404(
        db=db,
        file_id=file_id,
        current_user=current_user,
    )

    version_to_restore = get_file_version_or_404(
        db=db,
        file_id=file_id,
        version_number=version_number,
        current_user=current_user,
    )

    source_path = Path(version_to_restore.stored_path)

    storage = get_storage_backend()

    # If the source path for the version to restore does not exist, raise an HTTP 404 Not Found exception indicating that the file version is not found
    if not storage.exists(version_to_restore.stored_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File version not found",
        )

    stored_filename, stored_path, size = storage.copy_file(
        source_path=source_path,
        user_id=current_user.id,
        original_filename=version_to_restore.original_filename,
    )

    # Attempt to create a new FileVersion record for the restored version, update the current file record, and commit the changes to the database. If any exception occurs, roll back the transaction and delete the copied file from local storage to maintain data integrity.
    try:
        latest_version_number = db.scalar(
            select(func.max(FileVersion.version_number)).where(
                FileVersion.file_id == file_record.id
            )
        )

        next_version_number = (latest_version_number or 0) + 1

        restored_version = FileVersion(
            file_id=file_record.id,
            version_number=next_version_number,
            original_filename=version_to_restore.original_filename,
            stored_filename=stored_filename,
            stored_path=stored_path,
            content_type=version_to_restore.content_type,
            size=size,
        )

        file_record.original_filename = version_to_restore.original_filename
        file_record.stored_filename = stored_filename
        file_record.stored_path = stored_path
        file_record.content_type = version_to_restore.content_type
        file_record.size = size

        db.add(restored_version)
        db.commit()
        db.refresh(restored_version)

        return restored_version
        
    # If any exception occurs during the restoration process, roll back the database transaction and delete the copied file from local storage to maintain data integrity
    except Exception:
        db.rollback()

        storage.delete_file(stored_path)

        raise