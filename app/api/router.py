from fastapi import APIRouter

from app.api.routes import auth, health, users, files, shares

# Define main API router
api_router = APIRouter()

# Include all routes
api_router.include_router(auth.router)
api_router.include_router(health.router)
api_router.include_router(users.router)
api_router.include_router(files.router)
api_router.include_router(shares.router)
