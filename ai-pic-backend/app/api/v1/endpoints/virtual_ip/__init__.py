from fastapi import APIRouter

from .ai import router as ai_router
from .crud import router as crud_router

router = APIRouter()
router.include_router(crud_router, prefix="/virtual-ips")
router.include_router(ai_router, prefix="/virtual-ips")

__all__ = ["router"]
