from datetime import datetime, timedelta, timezone
from pathlib import Path
import secrets

from fastapi import HTTPException, status
from fastapi.responses import FileResponse as FastAPIFileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.file_share import FileShare
from app.models.user import User
from app.services.file_service import get_user_file_or_404
from app.storage.provider import get_storage_backend

# Service function to create a shareable link for a specific file, ensuring it belongs to the current user and setting an expiration time for the share link
def create_file_share(
    db: Session,
    file_id: int,
    current_user: User,
    expires_in_hours: int,
) -> FileShare:
    # Retrieve the file record for the specified file ID, ensuring it belongs to the current user
    file_record = get_user_file_or_404(
        db=db, 
        file_id=file_id, 
        current_user=current_user,
    )

    # Create a new FileShare record with a unique token, the file ID, and an expiration time based on the provided duration in minutes
    share = FileShare(
        token=secrets.token_urlsafe(32),
        file_id=file_record.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=expires_in_hours),
    )

    # Add the new FileShare record to the database session and commit the transaction
    db.add(share)
    db.commit()
    db.refresh(share)

    return share

# Service function to list all shareable links for a specific file, ensuring it belongs to the current user
def list_file_shares(
    db: Session,
    file_id: int,
    current_user: User,
) -> list[FileShare]:
    # Retrieve the file record for the specified file ID, ensuring it belongs to the current user
    file_record = get_user_file_or_404(
        db=db, 
        file_id=file_id, 
        current_user=current_user,
    )

    # Query the database for all FileShare records associated with the specified file ID, ordered by creation date in descending order
    return list(
        db.scalars(
            select(FileShare)
            .where(FileShare.file_id == file_record.id)
            .order_by(FileShare.created_at.desc())
        )
    )

# Service function to revoke a specific shareable link for a file, ensuring it belongs to the current user
def revoke_file_share(
    db: Session,
    file_id: int,
    share_id: int,
    current_user: User,
) -> None:
    file_record = get_user_file_or_404(
        db=db, 
        file_id=share_id, 
        current_user=current_user,
    )

    # Query the database for the specific FileShare record by its ID and ensure it is associated with the specified file ID
    share = db.scalar(
        select(FileShare)
        .where(FileShare.id == share_id, FileShare.file_id == file_record.id)
    )

    # If the share record is not found, raise an HTTP 404 Not Found exception
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share not found"
        )

    # Delete the share record from the database and commit the transaction
    db.delete(share)
    db.commit()

# Service function to download a shared file using a share token, ensuring the share link is valid and has not expired
def download_shared_file(
    db: Session,
    token: str,
) -> FastAPIFileResponse:
    
    now = datetime.now(timezone.utc)

    # Query the database for the FileShare record associated with the provided token and ensure it has not expired
    share = db.scalar(
        select(FileShare).where(
            FileShare.token == token,
            FileShare.expires_at > now,
        )
    )

    # If the share record is not found or has expired, raise an HTTP 404 Not Found exception
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shared file not found",
        )

    # Retrieve the associated file record for the share link
    file_record = share.file
    file_path = Path(file_record.stored_path)

    storage = get_storage_backend()

    if not storage.exists(file_record.stored_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shared file not found",
        )

    # Return a FastAPI FileResponse object to facilitate file download, using the stored path and original filename, along with headers to prevent caching of the shared file
    return FastAPIFileResponse(
        path=Path(file_record.stored_path),
        filename=file_record.original_filename,
        media_type=file_record.content_type,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )