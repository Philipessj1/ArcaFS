from fastapi import (
    Depends, 
    UploadFile,
    status,
    File as FastAPIFile,
    HTTPException,
    APIRouter,
)
from fastapi.responses import FileResponse as FastAPIFileResponse
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from pathlib import Path

from app.auth.dependencies import get_current_user
from app.database.dependencies import get_db
from app.models.user import User
from app.models.file import File
from app.models.file_version import FileVersion
from app.schemas.file_version import FileVersionResponse
from app.storage.local import copy_file_locally, save_file_locally
from app.storage.validation import validate_upload_file


router = APIRouter()

# Endpoint to upload and register a new version of an existing file
@router.post(
    "/{file_id}/versions",
    response_model=FileVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_new_file_version(
    file_id: int,
    file: UploadFile = FastAPIFile(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Query the database for the file with the given ID and owned by the current user
    file_record = db.scalar(
        select(File).where(
            File.id == file_id,
            File.owner_id == current_user.id,
        )
    )

    # Check if the core file record exists; if not, raise a 404 error
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    validate_upload_file(file)

    # Save the new file version locally and get its stored filename, path, and size
    stored_filename, stored_path, size = save_file_locally(
        upload_file=file,
        user_id=current_user.id,
    )

    # Fallback to a default name if the uploaded file lacks an original filename
    original_filename = file.filename or "unnamed_file"

    # Query the highest current version number for this file, defaulting to 0 if none exist
    current_version_number = db.scalar(
        select(func.max(FileVersion.version_number)).where(
            FileVersion.file_id == file_record.id
        )
    ) or 0

    # Increment the version counter for the new record
    next_version_number = current_version_number + 1

    try:
        # Initialize the tracking record for this specific file version
        new_version = FileVersion(
            file_id=file_record.id,
            version_number=next_version_number,
            original_filename=original_filename,
            stored_filename=stored_filename,
            stored_path=stored_path,
            content_type=file.content_type,
            size=size,
        )

        db.add(new_version)

        # Update the parent file record to reflect the metadata of the latest version
        file_record.original_filename = original_filename
        file_record.stored_filename = stored_filename
        file_record.stored_path = stored_path
        file_record.content_type = file.content_type
        file_record.size = size

        # Commit both the new version entry and parent file updates to the database
        db.commit()
        db.refresh(new_version)

    # Handle database exceptions by rolling back and cleaning up the physical file from storage
    except SQLAlchemyError:
        db.rollback()

        # Check if the file was written to disk and delete it to prevent orphaned files
        saved_file_path = Path(stored_path)
        if saved_file_path.is_file():
            saved_file_path.unlink()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create file version.",
        )

    return new_version

# Endpoint to list all versions of a specific file ordered by version number
@router.get(
    "/{file_id}/versions",
    response_model=list[FileVersionResponse],  # Ajustado de [FileVersionResponse] para list[...]
)
def list_file_versions(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Query the database for the file with the given ID and owned by the current user
    file_record = db.scalar(
        select(File).where(
            File.id == file_id,
            File.owner_id == current_user.id,
        )
    )

    # Check if the core file record exists; if not, raise a 404 error
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )
    
    # Query the database for all versions associated with the file, ordered by latest version first
    versions = db.scalars(
        select(FileVersion)
        .where(FileVersion.file_id == file_record.id)
        .order_by(FileVersion.version_number.desc())
    ).all()

    return versions

# Endpoint to download a specific version of a file by its version number
@router.get("/{file_id}/versions/{version_number}/download")
def download_file_version(
    file_id: int,
    version_number: int,
    curent_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Query the database for the specific file version, ensuring the parent file belongs to the current user
    version = db.scalar(
        select(FileVersion)
        .join(File)
        .where(
            FileVersion.file_id == file_id,
            FileVersion.version_number == version_number,
            File.owner_id == curent_user.id,
        )
    )

    # Check if the file version record exists; if not, raise a 404 error
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File version not found",
        )
    
    # Resolve the physical path of the specific file version from the database record
    file_path = Path(version.stored_path)

    # Check if the physical file version actually exists in storage; if not, raise a 404 error
    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File version is missing from storage",
        )
    
    # Return the file version as a response with appropriate cache control headers to prevent client-side caching
    return FastAPIFileResponse(
        path=file_path,
        media_type=version.content_type or "application/octet-stream",
        filename=version.original_filename,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )

# Endpoint to restore an older file version by duplicating it as the newest version
@router.post(
    "/{file_id}/versions/{version_number}/restore",
    response_model=FileVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
def restore_file_version(
    file_id: int,
    version_number: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Query the database for the core file record owned by the current user
    file_record = db.scalar(
        select(File).where(
            File.id == file_id,
            File.owner_id == current_user.id,
        )
    )

    # Check if the core file record exists; if not, raise a 404 error
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    # Query the database for the specific historical version targeted for restoration
    version_to_restore = db.scalar(
        select(FileVersion).where(
            FileVersion.file_id == file_record.id,
            FileVersion.version_number == version_number,
        )
    )

    # Check if the targeted file version record exists; if not, raise a 404 error
    if not version_to_restore:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File version not found",
        )

    # Resolve and validate the physical path of the targeted historical version on disk
    source_path = Path(version_to_restore.stored_path)

    # Check if the physical version file actually exists in storage; if not, raise a 404 error
    if not source_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File version is missing from storage",
        )

    # Initialize path tracking variable for potential rollback cleanup
    stored_path: str | None = None

    # Attempt to duplicate the file binary and append a new version entry within a single transaction
    try:
        # Create a physical copy of the historical file under a new unique filename
        stored_filename, stored_path, size = copy_file_locally(
            source_path=version_to_restore.stored_path,
            user_id=current_user.id,
            original_filename=version_to_restore.original_filename,
        )

        # Query the highest current version number for this file to compute the next increment
        current_version_number = db.scalar(
            select(func.max(FileVersion.version_number)).where(
                FileVersion.file_id == file_record.id
            )
        ) or 0

        # Increment the version counter for the restored record
        next_version_number = current_version_number + 1

        # Initialize the new tracking record representing the restored file version
        restored_version = FileVersion(
            file_id=file_record.id,
            version_number=next_version_number,
            original_filename=version_to_restore.original_filename,
            stored_filename=stored_filename,
            stored_path=stored_path,
            content_type=version_to_restore.content_type,
            size=size,
        )

        db.add(restored_version)

        # Update the core file record to mirror and track this newly restored version
        file_record.original_filename = version_to_restore.original_filename
        file_record.stored_filename = stored_filename
        file_record.stored_path = stored_path
        file_record.content_type = version_to_restore.content_type
        file_record.size = size

        # Commit both the restored version entry and parent file updates to the database
        db.commit()
        db.refresh(restored_version)

    # Handle system or database exceptions by rolling back and cleaning up the duplicated file
    except (SQLAlchemyError, OSError):
        db.rollback()

        # If a new file was successfully written to disk before the error, ensure it is deleted
        if stored_path:
            copied_file = Path(stored_path)

            if copied_file.is_file():
                copied_file.unlink()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not restore file version",
        )

    return restored_version
