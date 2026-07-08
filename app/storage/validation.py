from fastapi import UploadFile, status, HTTPException

from app.core.config import (
    MAX_UPLOAD_SIZE_BYTES, 
    ALLOWED_CONTENT_TYPES,
)

# Guard function to validate raw file stream attributes before memory processing or storage allocation
def validate_upload_file(upload_file: UploadFile) -> None:
    # Assert that the filename attribute is populated to prevent anonymous stream binding issues
    if not upload_file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File name is required",
    )

    # Enforce strict mimetype white-listing against the global platform whitelist
    if upload_file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File type is not allowed",
    )

    # Move the file stream cursor to the absolute end (offset 0, whence 2) to calculate byte depth
    upload_file.file.seek(0, 2)
    
    # Query the exact position indicator integer value which translates directly to file size in bytes
    file_size = upload_file.file.tell()
    
    # Rewind the stream cursor position back to the origin (offset 0) so sequential reads do not return empty data
    upload_file.file.seek(0)

    # Enforce strict upper-bound multi-part request body volumetric constraints
    if file_size > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="File exceeds the 10 MB upload limit",
    )