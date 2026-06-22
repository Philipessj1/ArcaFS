from fastapi import APIRouter
from sqlalchemy import text

from app.database.database import engine

# Initialize API router for health check endpoints
router = APIRouter(tags=["Health"])

# Basic health check endpoints
@router.get("/")
def root():
    return {"message": "Welcome to ArcaFS"}

@router.get("/health")
def health():
    return {"status": "ok"}

@router.get("/db-test")
def db_test():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return {"db_test": result.scalar()}