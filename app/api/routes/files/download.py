from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse as FastAPIFileResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.dependencies import get_db
from app.models.user import User
from app.services.file_service import download_user_file

router = APIRouter()

# Endpoint to download a specific file by its ID
@router.get(
    "/{file_id}/download",
    response_class=FastAPIFileResponse,
    )
def download_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return download_user_file(
        db=db,
        file_id=file_id,
        current_user=current_user,
    )