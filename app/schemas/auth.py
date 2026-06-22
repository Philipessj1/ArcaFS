from pydantic import BaseModel, EmailStr

# Schemas for authentication
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
