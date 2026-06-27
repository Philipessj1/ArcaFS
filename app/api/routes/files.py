from fastapi import (
    APIRouter, 
    Depends, 
    UploadFile,
    status,
    File as FastAPIFile,
    HTTPException,
    Response,
    Request,
)
from fastapi.responses import FileResponse as FastAPIFileResponse
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from pathlib import Path
from datetime import datetime, timedelta, timezone
import secrets

from app.auth.dependencies import get_current_user
from app.database.dependencies import get_db
from app.models.user import User
from app.models.file import File
from app.models.file_share import FileShare
from app.models.file_version import FileVersion
from app.schemas.file import FileResponse
from app.schemas.share import FileShareResponse, ShareCreate
from app.schemas.file_version import FileVersionResponse
from app.storage.local import save_file_locally
from app.storage.validation import validate_upload_file

# Define the router for file-related endpoints
router = APIRouter(
    prefix="/files",
    tags=["files"],
)

# Endpoint to handle file uploads
@router.post(
    "/upload",
    response_model=FileResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_file(
    file: UploadFile = FastAPIFile(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):  
    # Validate file before saving
    validate_upload_file(file)

    # Save the uploaded file locally and get its stored filename, path, and size
    stored_filename, stored_path, size = save_file_locally(
        upload_file=file, 
        user_id=current_user.id
    )

    original_filename = file.filename or "unnamed_file"

    # Initialize the core File database model with metadata
    uploaded_file = File(
        original_filename=file.filename or "unnamed_file",
        stored_filename=stored_filename,
        stored_path=stored_path,
        content_type=file.content_type,
        size=size,
        owner_id=current_user.id,
    )

    try:
        # Stage the file record and flush to generate its primary key ID
        db.add(uploaded_file)
        db.flush()

        # Initialize the tracking record for the first version of this file
        initial_version = FileVersion(
            file_id=uploaded_file.id,
            version_number=1,
            original_filename=original_filename,
            stored_filename=stored_filename,
            stored_path=stored_path,
            content_type=file.content_type,
            size=size,
        )

        db.add(initial_version)
        db.commit()
        db.refresh(uploaded_file)

    # Handle database exceptions by rolling back and cleaning up the physical file from storage
    except SQLAlchemyError:
        db.rollback()

        saved_file_path = Path(stored_path)
        if saved_file_path.is_file():
            saved_file_path.unlink()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save file metadata",
        )

    return uploaded_file

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

# Endpoint to list all files uploaded by the current user
@router.get("/", response_model=list[FileResponse])
def list_user_files(
    curent_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):  
    # Query the database for files owned by the current user, ordered by creation date
    files = db.scalars(
        select(File)
        .where(File.owner_id == curent_user.id)
        .order_by(File.created_at.desc())
    ).all()

    return files

# Endpoint to download a specific file by its ID
@router.get("/{file_id}/download")
def download_file(
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
    
    # Check if the file record exists; if not, raise a 404 error
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    # Check if the file exists in the storage; if not, raise a 404 error
    file_path = Path(file_record.stored_path)

    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File is missing from storage.",
        )

    # Return the file as a response with the appropriate media type and filename
    return FastAPIFileResponse(
        path=file_path,
        media_type=file_record.content_type or "application/octet-stream",
        filename=file_record.original_filename,
)

# Endpoint to delete a specific file by its ID
@router.delete(
    "/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_file(
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

    # Check if the file record exists; if not, raise a 404 error
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    # Check if the file exists in the storage; if it does, delete it
    file_path = Path(file_record.stored_path)

    # Attempt to delete the file from storage
    try:
        if file_path.exists():
            file_path.unlink()

        # Delete the file record from the database
        db.delete(file_record)
        db.commit()

    # Handle any OSError that may occur during file deletion and rollback the database transaction
    except OSError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not delete the file from storage.",
        )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# Endpoint to create a shareable link for a specific file
@router.post(
    "/{file_id}/share",
    response_model=FileShareResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_file_share(
    file_id: int,
    share_data: ShareCreate,
    request: Request,
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

    # Check if the file record exists; if not, raise a 404 error
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )
    
    # Calculate the expiration timestamp based on the requested hours
    expires_at = datetime.now(timezone.utc) + timedelta(
        hours=share_data.expires_in_hours
    )

    # Create a new FileShare record with a secure, unique token
    share = FileShare(
        token=secrets.token_urlsafe(32),
        file_id=file_record.id,
        expires_at=expires_at,
    )

    # Save the share record to the database
    db.add(share)
    db.commit()
    db.refresh(share)

    # Generate the absolute sharing URL using the application's base URL
    base_url = str(request.base_url).rstrip("/")
    share_url = f"{base_url}/shared/{share.token}"

    # Return the file share details including the generated link and expiration date
    return FileShareResponse(
        id=share.id,
        share_url=share_url,
        expires_at=share.expires_at,
        created_at=share.created_at,
    )

# Endpoint to list all active or expired share links for a specific file
@router.get(
    "/{file_id}/shares",
    response_model=list[FileShareResponse]
)
def list_file_shares(
    file_id: int,
    request: Request,
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

    # Check if the file record exists; if not, raise a 404 error
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not Found",
        )
    
    # Query the database for all share links associated with the file, ordered by creation date
    shares = db.scalars(
        select(FileShare)
        .where(FileShare.file_id == file_record.id)
        .order_by(FileShare.created_at.desc())
    ).all()

    # Get the application's base URL to construct absolute sharing links
    base_url = str(request.base_url).rstrip("/")

    # Construct and return the full list of file share responses with public URLs
    return [
        FileShareResponse(
            id=share.id,
            share_url=f"{base_url}/shared/{share.token}",
            expires_at=share.expires_at,
            created_at=share.created_at,
        )
        for share in shares
    ]

# Endpoint to revoke and delete a specific share link
@router.delete(
    "/{file_id}/shares/{share_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def revoke_file_share(
    file_id: int,
    share_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Query the database for the specific share link, ensuring the file belongs to the current user
    share = db.scalar(
        select(FileShare)
        .join(File)
        .where(
            FileShare.id == share_id,
            FileShare.file_id == file_id,
            File.owner_id == current_user.id,
        )
    )

    # Check if the share record exists; if not, raise a 404 error
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share link not found",
        )
    
    # Delete the share record from the database
    db.delete(share)
    db.commit()
    
    # Return a 204 No Content response to confirm deletion
    return Response(status_code=status.HTTP_204_NO_CONTENT)