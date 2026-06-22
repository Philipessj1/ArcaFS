from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.security import (
    create_access_token,
    hash_password,
    verify_password,
)

from app.database.dependencies import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate

# Define API router for authentication endpoints
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

# User registration endpoint
@router.post(
    "/register", 
    status_code=status.HTTP_201_CREATED
    )
def register_user(
    user_data: UserCreate, 
    db: Session = Depends(get_db)
 ):
    existing_user = db.scalar(
        select(User).where(User.email == user_data.email)
    )

    # Check if user with the same email already exists  
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    # Create new user and save to database
    user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hash_password(user_data.password)
    )

    # Save user to database
    db.add(user)
    db.commit()
    db.refresh(user)

    # Return user info (excluding password hash)
    return {
        "id": user.id, 
        "name": user.name, 
        "email": user.email
        }

# User login endpoint
@router.post("/login", response_model=TokenResponse)
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db),
):  
    # Retrieve user from database based on email
    user = db.scalar(
        select(User).where(User.email == credentials.email)
    )

    # Verify user exists and password is correct
    if not user or not verify_password(
        credentials.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
    )

    # Create JWT access token for authenticated user
    access_token = create_access_token(subject=str(user.id))

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }
