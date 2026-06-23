from fastapi import FastAPI

from app.api.router import api_router
from app.models.file import File
from app.models.user import User

# Initialize FastAPI app
app = FastAPI(
    title="ArcaFS API",
    description="Cloud File Storage API built with FastAPI",
    version="0.1.0",
)

# Include API router
app.include_router(api_router)
