from abc import ABC, abstractmethod
from pathlib import Path

from fastapi import UploadFile

# Abstract base class for storage backends, defining the interface for saving files and managing storage operations
class StorageBackend(ABC):
    
    @abstractmethod
    def save_file(
        self,
        upload_file: UploadFile,
        user_id: int,
    ) -> tuple[str, str, int]:
        # Save a file and return the stored filename, path, and size
        pass

    @abstractmethod
    def copy_file(
        self,
        source_path: Path,
        user_id: int,
        original_filename: str,
    ) -> tuple[str, str, int]:
        # Copy a file from a source path to the storage backend and return the stored filename, path, and size
        pass

    @abstractmethod
    def delete_file(
        self,
        stored_path: str,
    ) -> None:
        # Delete a file from the storage backend given its stored path
        pass

    @abstractmethod
    def exists(
        self,
        stored_path: str,
    ) -> bool:
        # Check if a file exists in the storage backend given its stored path
        pass
    
    def download_to_temp_file(
        self,
        stored_path: str,
    ) -> Path:
        # Download a file from the storage backend to a temporary local file and return the path to the temporary file
        return Path(stored_path)

    def should_cleanup_download_file(self) -> bool:
        # Tells if download_to_temp_file have to be removed after the response
        return False