from pathlib import Path
from uuid import uuid4

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