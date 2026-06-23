from fastapi import (
    APIRouter, 
    Depends, 
    UploadFile,
    status,
    File as FastAPIFile,
    HTTPException,
    Response,
)
from fastapi.responses import FileResponse as FastAPIFileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from pathlib import Path

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
