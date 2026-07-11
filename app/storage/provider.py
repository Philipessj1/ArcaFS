from fastapi import HTTPException, status

from app.core.config import STORAGE_BACKEND
from app.storage.base import StorageBackend
from app.storage.local import LocalStorage

# Function to get the current storage backend. This can be modified to return different backends based on configuration or environment.
def get_storage_backend() -> StorageBackend:
    # Currently, we are using LocalStorage as the storage backend. This can be changed to other backends in the future.
    if STORAGE_BACKEND == "local":
        return LocalStorage()
    
    # If the STORAGE_BACKEND is not recognized, raise an HTTPException indicating that the storage backend is unsupported.
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Unsupported storage backend: {STORAGE_BACKEND}",
    )