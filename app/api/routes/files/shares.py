from fastapi import (
    APIRouter, 
    Depends, 
    status,
    HTTPException,
    Response,
    Request,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from datetime import datetime, timedelta, timezone
import secrets

from app.auth.dependencies import get_current_user
from app.database.dependencies import get_db
from app.models.user import User
from app.models.file import File
from app.models.file_share import FileShare
from app.schemas.share import FileShareResponse, ShareCreate

router = APIRouter()

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
