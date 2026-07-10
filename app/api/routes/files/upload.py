from fastapi import (
    APIRouter,
    UploadFile,
    File as FastAPIFile,
    status,
    Depends
)
from sqlalchemy.orm import Session
from app.auth.dependencies import get_current_user
from app.database.dependencies import get_db
from app.models.user import User
from app.schemas.file import FileResponse
from app.services.file_service import upload_file as upload_file_service

router = APIRouter()

# Endpoint to handle file uploads
@router.post(
    "/upload",
    response_model=FileResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_user_file(
    upload_file: UploadFile = FastAPIFile(..., alias="file"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):  
    # Delegate the file upload process to the service layer, which handles validation, storage, and database registration
    return upload_file_service(
        db=db,
        upload_file=upload_file,
        current_user=current_user,
    )