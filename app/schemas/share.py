from datetime import datetime

from pydantic import BaseModel, Field

# Schemas for share file link
class ShareCreate(BaseModel):
    expires_in_hours: int = Field(
        default=24,
        ge=1,
        le=168,
        description="How long the share link remains valid, in hours",
    )

class FileShareResponse(BaseModel):
    id: int
    share_url: str
    expires_at: datetime
    created_at: datetime
