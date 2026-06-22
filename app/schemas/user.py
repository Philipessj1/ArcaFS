from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

# Schemas for User
class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: datetime
