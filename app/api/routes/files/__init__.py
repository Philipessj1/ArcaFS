from fastapi import APIRouter

from app.api.routes.files import (
    download,
    management,
    shares,
    upload,
    versions,
)

router = APIRouter(
    prefix="/files",
    tags=["Files"],
)

router.include_router(upload.router)
router.include_router(management.router)
router.include_router(download.router)
router.include_router(shares.router)
router.include_router(versions.router)