from fastapi import FastAPI

from app.database.base import Base
from app.database.database import engine
from app.api.router import api_router

# Temporarily create database tables on startup (for development)
# Alembic will be used for migrations in production
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="ArcaFS API",
    description="Cloud File Storage API built with FastAPI",
    version="0.1.0",
)

# Include API router
app.include_router(api_router)
