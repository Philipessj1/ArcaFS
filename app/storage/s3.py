from pathlib import Path
import tempfile
import uuid

import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException, UploadFile, status

from app.core.config import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_REGION,
    AWS_S3_BUCKET_NAME,
)
from app.storage.base import StorageBackend

# S3Storage class that implements the StorageBackend interface for AWS S3 storage.
class S3Storage(StorageBackend):

    # Initialize the S3Storage class and check if the AWS_S3_BUCKET_NAME is configured.
    def __init__(self) -> None:
        if not AWS_S3_BUCKET_NAME:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="AWS_S3_BUCKET_NAME is not configured.",
            )
        
        # Set the bucket name and create an S3 client using the provided AWS credentials and region.
        self.bucket_name = AWS_S3_BUCKET_NAME

        self.s3_client = boto3.client(
            "s3",
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )
    
    # Save the uploaded file to S3 storage and return the stored filename, path, and size.
    def save_file(
        self,
        upload_file: UploadFile,
        user_id: int,
    ) -> tuple[str, str, int]:

        # Generate a unique filename for the uploaded file using a UUID and the original file extension.
        extension = Path(upload_file.filename or "").suffix
        stored_filename = f"{uuid.uuid4()}{extension}"
        object_key = f"users/{user_id}/files/{stored_filename}"

        # Move the file pointer to the end of the file to get its size, then reset it back to the beginning.
        upload_file.file.seek(0, 2)
        size = upload_file.file.tell()
        upload_file.file.seek(0)

        # Upload the file to S3 using the S3 client.
        try:
            self.s3_client.upload_fileobj(
                Fileobj=upload_file.file,
                Bucket=self.bucket_name,
                Key=object_key,
                ExtraArgs={
                    "ContentType": upload_file.content_type or "application/octet-stream",
                },
            )
        
        except ClientError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file to S3",
            ) from exc
        
        return stored_filename, object_key, size
    
    # Copy a file from one location in S3 to another, returning the new stored filename, path, and size.
    def copy_file(
        self,
        source_path: Path,
        user_id: int,
        original_filename: str,
    ) -> tuple[str, str, int]:
        
        source_key = str(source_path)

        extension = Path(original_filename).suffix
        stored_filename = f"{uuid.uuid4()}{extension}"
        destination_key = f"users/{user_id}/files/{stored_filename}"

        # Retrieve the metadata of the source object to get its content type and size, then copy the object to the new destination in S3.
        try:
            metadata = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=source_key,
            )

            self.s3_client.copy_object(
                Bucket=self.bucket_name,
                CopySource={
                    "Bucket": self.bucket_name,
                    "Key": source_key
                },
                Key=destination_key,
                ContentType=metadata.get("ContentType", "application/octet-stream"),
                MetadataDirective="REPLACE",
            )

            size = metadata["ContentLength"]

        except ClientError as exc:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to copy file in S3",
                ) from exc

        return stored_filename, destination_key, size
    
    # Delete a file from S3 storage based on its stored path.
    def delete_file(
        self,
        stored_path: str,
    ) -> None:

        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=stored_path,
            )

        except ClientError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete file from S3",
            ) from exc
    
    # Check if a file exists in S3 storage based on its stored path, returning True if it exists and False otherwise.
    def exists(
        self,
        stored_path: str,
    ) -> bool:
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=stored_path,
            )
            return True
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")

            if error_code in ("404", "NoSuchKey", "NotFound"):
                return False

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to check file existence in S3",
            ) from exc

    # Download a file from S3 storage to a temporary local file and return the path to the temporary file.
    def download_to_temp_file(
        self,
        stored_path: str,
    ) -> Path:
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_path = Path(temp_file.name)
        temp_file.close()  # Close the file so that boto3 can write to it

        # Attempt to download the file from S3 to the temporary file. If the download fails, clean up the temporary file and raise an HTTPException.
        try: 
            self.s3_client.download_file(
                Bucket=self.bucket_name,
                Key=stored_path,
                Filename=str(temp_path),
            )
        except ClientError as exc:
            if temp_path.exists():
                temp_path.unlink()
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to download file from S3",
            ) from exc

        return temp_path
    
    def should_cleanup_download_file(self) -> bool:
        return True