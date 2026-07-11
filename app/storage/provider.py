from app.storage.base import StorageBackend
from app.storage.local import LocalStorage

# Function to get the current storage backend. This can be modified to return different backends based on configuration or environment.
def get_storage_backend() -> StorageBackend:
    # Currently, we are using LocalStorage as the storage backend. This can be changed to other backends in the future.
    return LocalStorage()