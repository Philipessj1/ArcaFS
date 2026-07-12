from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import AWS_S3_BUCKET_NAME
from app.storage.base import StorageBackend

class S3Storage(StorageBackend):
    # Initialize the S3Storage class and check if the AWS_S3_BUCKET_NAME is configured.
    def __init__(self) -> None:
        if not AWS_S3_BUCKET_NAME:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="AWS_S3_BUCKET_NAME is not configured.",
            )
    
    def save_file(
        self,
        source_path: Path,
        user_id: int,
        original_filename: str,
    ) -> tuple[str, str, int]:
        raise NotImplementedError(
            "S3 save_file is not implemented yet."
        )
    
    def copy_file(
        self,
        source_path: Path,
        user_id: int,
        original_filename: str,
    ) -> tuple[str, str, int]:
        raise NotImplementedError(
            "S3 copy_file is not implemented yet."
        )
    
    def delete_file(
        self,
        stored_path: str,
    ) -> None:
        raise NotImplementedError(
            "S3 delete_file is not implemented yet."
        )
    
    def exists(
        self,
        stored_path: str,
    ) -> bool:
        raise NotImplementedError(
            "S3 exists is not implemented yet."
        )