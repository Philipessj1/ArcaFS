from pathlib import Path
import shutil
import uuid

from fastapi import UploadFile

from app.storage.base import StorageBackend


UPLOADS_DIR = Path("storage/uploads")


class LocalStorage(StorageBackend):
    # Implement the abstract methods defined in StorageBackend for local file storage
    def save_file(
        self,
        upload_file: UploadFile,
        user_id: int,
    ) -> tuple[str, str, int]:
        user_upload_dir = UPLOADS_DIR / str(user_id)
        user_upload_dir.mkdir(parents=True, exist_ok=True)

        extension = Path(upload_file.filename or "").suffix
        stored_filename = f"{uuid.uuid4()}{extension}"
        stored_path = user_upload_dir / stored_filename

        content = upload_file.file.read()

        with stored_path.open("wb") as file_buffer:
            file_buffer.write(content)

        size = stored_path.stat().st_size

        upload_file.file.seek(0)

        return stored_filename, str(stored_path), size

    # Implement the copy_file method to copy a file from a source path to the local storage backend
    def copy_file(
        self,
        source_path: Path,
        user_id: int,
        original_filename: str,
    ) -> tuple[str, str, int]:
        user_upload_dir = UPLOADS_DIR / str(user_id)
        user_upload_dir.mkdir(parents=True, exist_ok=True)

        extension = Path(original_filename).suffix
        stored_filename = f"{uuid.uuid4()}{extension}"
        destination_path = user_upload_dir / stored_filename

        shutil.copy2(source_path, destination_path)

        size = destination_path.stat().st_size

        return stored_filename, str(destination_path), size

    # Implement the delete_file method to delete a file from the local storage backend given its stored path
    def delete_file(
        self,
        stored_path: str,
    ) -> None:
        file_path = Path(stored_path)

        if file_path.exists():
            file_path.unlink()
            
    # Implement the exists method to check if a file exists in the local storage backend given its stored path
    def exists(
        self,
        stored_path: str,
    ) -> bool:
        return Path(stored_path).exists()
    
    # Implement the download_to_temp_file method to return the path to a temporary local file for downloading
    def download_to_temp_file(
        self,
        stored_path: str,
    ) -> Path:
        return Path(stored_path)

# Old functions that use LocalStorage directly, can be refactored to use dependency injection for better testability and flexibility in the future.
def save_file_locally(
    upload_file: UploadFile,
    user_id: int,
) -> tuple[str, str, int]:
    return LocalStorage().save_file(
        upload_file=upload_file,
        user_id=user_id,
    )


def copy_file_locally(
    source_path: Path,
    user_id: int,
    original_filename: str,
) -> tuple[str, str, int]:
    return LocalStorage().copy_file(
        source_path=source_path,
        user_id=user_id,
        original_filename=original_filename,
    )