from fastapi import APIRouter, Depends, File as FastAPIFile, UploadFile, status
from fastapi.responses import FileResponse as FastAPIFileResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.dependencies import get_db
from app.models.user import User
from app.schemas.file_version import FileVersionResponse
from app.services.version_service import (
    create_new_file_version,
    download_file_version,
    list_file_versions,
    restore_file_version,
)


router = APIRouter()

# Endpoint to upload and register a new version of an existing file
@router.post(
    "/{file_id}/versions",
    response_model=FileVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_file_version(
    file_id: int,
    uploaded_file: UploadFile = FastAPIFile(..., alias="file"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_new_file_version(
        db=db,
        file_id=file_id,
        uploaded_file=uploaded_file,
        current_user=current_user,
    )

# Endpoint to list all versions of a specific file ordered by version number
@router.get(
    "/{file_id}/versions",
    response_model=list[FileVersionResponse],
)
def list_versions(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_file_versions(
        db=db,
        file_id=file_id,
        current_user=current_user,
    )

# Endpoint to download a specific version of a file by its version number
@router.get(
    "/{file_id}/versions/{version_number}/download",
    response_class=FastAPIFileResponse,
)
def download_version(
    file_id: int,
    version_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return download_file_version(
        db=db,
        file_id=file_id,
        version_number=version_number,
        current_user=current_user,
    )

# Endpoint to restore an older file version by duplicating it as the newest version
@router.post(
    "/{file_id}/versions/{version_number}/restore",
    response_model=FileVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
def restore_version(
    file_id: int,
    version_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return restore_file_version(
        db=db,
        file_id=file_id,
        version_number=version_number,
        current_user=current_user,
    )