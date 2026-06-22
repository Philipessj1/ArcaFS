from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.core.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    SECRET_KEY,
) 

# Initialize password hasher
password_hash = PasswordHash.recommended()

# Hashing and verifying passwords
def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)

# JWT token creation
def create_access_token(subject:str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    payload = {
        "sub": subject,
        "exp": expire,
    }

    return jwt.encode(
        payload, 
        SECRET_KEY, 
        algorithm=ALGORITHM
    )
