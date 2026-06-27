from pathlib import Path
from uuid import uuid4
from shutil import copy2

from fastapi import UploadFile

# Directory to store uploaded files
UPLOADS_DIR = Path("storage/uploads")

# Function to save uploaded files locally
def save_file_locally(
    upload_file: UploadFile,
    user_id: int,
) -> tuple[str, str, int]:

    # Create user-specific directory if it doesn't exist
    user_uploads_dir = UPLOADS_DIR / str(user_id)
    user_uploads_dir.mkdir(parents=True, exist_ok=True)

    # Determine the stored filename and path
    original_filename = upload_file.filename or "unnamed_file"

    extension = Path(original_filename).suffix
    stored_filename = f"{uuid4()}{extension}"

    file_path = user_uploads_dir / stored_filename

    # Read the content of the uploaded file and write it to the local storage
    content = upload_file.file.read()

    with file_path.open("wb") as destination:
        destination.write(content)

    # Return the stored filename, path, and size of the file
    return (
        stored_filename,
        str(file_path),
        len(content),
    )

def copy_file_locally(
    source_path: str,
    user_id: int,
    original_filename: str,
) -> tuple[str, str, int]:
    
    # Resolve the physical path of the source file
    source_file = Path(source_path)

    # Validate that the source file exists on disk before proceeding
    if not source_file.is_file():
        raise FileNotFoundError("Source file does not exist")
    
    # Ensure the user-specific upload directory exists, creating it if necessary
    user_upload_dir = UPLOADS_DIR / str(user_id)
    user_upload_dir.mkdir(parents=True, exist_ok=True)

    # Extract the file extension and generate a secure, unique filename using UUID4
    extension = Path(original_filename).suffix
    stored_filename = f"{uuid4()}{extension}"

    # Construct the absolute destination path for the copied file
    destination_path = user_upload_dir / stored_filename

    # Duplicate the file to the target location, preserving its original metadata
    copy2(source_file, destination_path)

    # Return a structured tuple containing the new filename, destination path, and file size
    return (
        stored_filename,
        str(destination_path),
        destination_path.stat().st_size,
    )