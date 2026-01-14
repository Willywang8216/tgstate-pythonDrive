from fastapi import APIRouter

from .files import router as files_router
from .settings import router as settings_router
from .sse import router as sse_router
from .upload import router as upload_router

router = APIRouter()

router.include_router(upload_router)
router.include_router(files_router)
router.include_router(sse_router)
router.include_router(settings_router)
