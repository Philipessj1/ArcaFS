from fastapi import FastAPI, Depends, HTTPException, status

from sqlalchemy import text, select
from sqlalchemy.orm import Session

from app.database.base import Base
from app.database.database import engine
from app.database.dependencies import get_db

from app.models.user import User

from app.schemas.user import UserCreate

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ArcaFS API",
    description="Cloud File Storage API built with FastAPI",
    version="0.1.0",
)

@app.get("/")
def root():
    return {"message": "Welcome to ArcaFS"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/db-test")
def db_test():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return {"db_test": result.scalar()}
    
@app.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.scalar(
        select(User).where(User.email == user_data.email)
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    user = User(
        name=user_data.name,
        email=user_data.email
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "id": user.id, 
        "name": user.name, 
        "email": user.email
        }
