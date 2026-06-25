from pydantic import BaseModel

# Token Schema
class TokenPayload(BaseModel):
    sub: str