from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.dependencies import get_db
from app.models.user import User
from app.schemas.file import FileResponse
from app.services.file_service import delete_user_file, list_user_files

router = APIRouter()

# Endpoint to list all files uploaded by the current user
@router.get("/", response_model=list[FileResponse])
def list_files(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):  
    return list_user_files(
        db=db,
        current_user=current_user,
        limit=limit,
        offset=offset
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
    delete_user_file(
        db=db,
        file_id=file_id,
        current_user=current_user,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
