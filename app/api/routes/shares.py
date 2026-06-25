from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.models.file_share import FileShare
from fastapi import Depends

# Define the router for public file sharing endpoints
router = APIRouter(tags=["Public Shares"])

# Endpoint to access and download a shared file via a unique token
@router.get("/shared/{token}")
def download_shared_file(
    token: str,
    db: Session = Depends(get_db),
):
    # Get the current time in UTC to check against expiration dates
    now = datetime.now(timezone.utc)

    # Query the database for an active share link that matches the token and has not expired
    share = db.scalar(
        select(FileShare).where(
            FileShare.token == token,
            FileShare.expires_at > now,
        )
    )

    # Check if the share link exists and is valid; if not, raise a 404 error
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shared file is missing from storage",
        )

    # Resolve the physical path of the file from the database record
    file_path = Path(share.file.stored_path)

    # Check if the physical file actually exists in storage; if not, raise a 404 error
    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shared file is missing from storage",
        )
    
    # Return the file as a response with its original metadata for the user to download
    return FileResponse(
        path=file_path,
        media_type=share.file.content_type or "application/octet-stream",
        filename=share.file.original_filename,
    )
