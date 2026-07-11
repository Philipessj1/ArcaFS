from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse as FastAPIFileResponse
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.services.share_service import download_shared_file

# Define the router for public file sharing endpoints
router = APIRouter(tags=["Public Shares"])

# Endpoint to access and download a shared file via a unique token
@router.get("/shared/{token}")
def download_shared_file_route(
    token: str,
    db: Session = Depends(get_db),
):
    return download_shared_file(
        db=db,
        token=token,
    )