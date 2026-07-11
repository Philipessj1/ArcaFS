from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.dependencies import get_db
from app.models.user import User
from app.schemas.share import FileShareResponse, ShareCreate
from app.services.share_service import (
    create_file_share,
    list_file_shares,
    revoke_file_share,
)

router = APIRouter()

# Endpoint to create a shareable link for a specific file
@router.post(
    "/{file_id}/share",
    response_model=FileShareResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_share_link(
    file_id: int,
    share_data: ShareCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    share = create_file_share(
        db=db,
        file_id=file_id,
        current_user=current_user,
        expires_in_hours=share_data.expires_in_hours,
    )

    # Return the share link details, including the generated URL for downloading the shared file
    return FileShareResponse(
        id=share.id,
        share_url=str(request.url_for("download_shared_file_route", token=share.token)),
        expires_at=share.expires_at,
        created_at=share.created_at,
    )

# Endpoint to list all shareable links for a specific file
@router.get(
    "/{file_id}/shares",
    response_model=list[FileShareResponse],
)
def list_share_links(
    file_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    shares = list_file_shares(
        db=db,
        file_id=file_id,
        current_user=current_user,
    )

    # Return a list of share link details, including the generated URLs for downloading the shared files
    return [
        FileShareResponse(
            id=share.id,
            share_url=str(request.url_for("download_shared_file_route", token=share.token)),
            expires_at=share.expires_at,
            created_at=share.created_at,
        )
        for share in shares
    ]

# Endpoint to revoke a specific shareable link for a file
@router.delete(
    "/{file_id}/shares/{share_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_share_link(
    file_id: int,
    share_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    revoke_file_share(
        db=db,
        file_id=file_id,
        share_id=share_id,
        current_user=current_user,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)