from fastapi import (
    APIRouter, 
    Depends, 
    status,
    HTTPException,
    Response,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from pathlib import Path

from app.auth.dependencies import get_current_user
from app.database.dependencies import get_db
from app.models.user import User
from app.models.file import File
from app.schemas.file import FileResponse

router = APIRouter()

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
