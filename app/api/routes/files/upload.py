from pathlib import Path

from fastapi import (
    APIRouter,
    HTTPException,
    UploadFile,
    File as FastAPIFile,
    status,
    Depends
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.auth.dependencies import get_current_user
from app.database.dependencies import get_db
from app.models.file import File
from app.models.file_version import FileVersion
from app.models.user import User
from app.schemas.file import FileResponse
from app.storage.local import save_file_locally
from app.storage.validation import validate_upload_file

router = APIRouter()

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
    # Validate file before saving
    validate_upload_file(file)

    # Save the uploaded file locally and get its stored filename, path, and size
    stored_filename, stored_path, size = save_file_locally(
        upload_file=file, 
        user_id=current_user.id
    )

    original_filename = file.filename or "unnamed_file"

    # Initialize the core File database model with metadata
    uploaded_file = File(
        original_filename=file.filename or "unnamed_file",
        stored_filename=stored_filename,
        stored_path=stored_path,
        content_type=file.content_type,
        size=size,
        owner_id=current_user.id,
    )

    try:
        # Stage the file record and flush to generate its primary key ID
        db.add(uploaded_file)
        db.flush()

        # Initialize the tracking record for the first version of this file
        initial_version = FileVersion(
            file_id=uploaded_file.id,
            version_number=1,
            original_filename=original_filename,
            stored_filename=stored_filename,
            stored_path=stored_path,
            content_type=file.content_type,
            size=size,
        )

        db.add(initial_version)
        db.commit()
        db.refresh(uploaded_file)

    # Handle database exceptions by rolling back and cleaning up the physical file from storage
    except SQLAlchemyError:
        db.rollback()

        saved_file_path = Path(stored_path)
        if saved_file_path.is_file():
            saved_file_path.unlink()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save file metadata",
        )

    return uploaded_file
