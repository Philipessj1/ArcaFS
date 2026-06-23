from fastapi import (
    APIRouter, 
    Depends, 
    UploadFile,
    status,
    File as FastAPIFile,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.dependencies import get_db
from app.models.user import User
from app.models.file import File
from app.schemas.file import FileResponse
from app.storage.local import save_file_locally

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
    # Save the uploaded file locally and get its stored filename, path, and size
    stored_filename, stored_path, size = save_file_locally(
        upload_file=file, 
        user_id=current_user.id
    )

    uploaded_file = File(
        original_filename=file.filename or "unnamed_file",
        stored_filename=stored_filename,
        stored_path=stored_path,
        content_type=file.content_type,
        size=size,
        owner_id=current_user.id,
    )

    db.add(uploaded_file)
    db.commit()
    db.refresh(uploaded_file)

    return uploaded_file

@router.get("/", response_model=list[FileResponse])
def list_user_files(
    curent_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    files = db.scalars(
        select(File)
        .where(File.owner_id == curent_user.id)
        .order_by(File.created_at.desc())
    ).all()

    return files
