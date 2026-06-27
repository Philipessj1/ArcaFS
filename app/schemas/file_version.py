from datetime import datetime

from pydantic import BaseModel

class FileVersionResponse(BaseModel):
    id: int
    file_id: int
    version_number: int
    original_filename: str
    content_type: str | None
    size: int
    created_at: datetime
