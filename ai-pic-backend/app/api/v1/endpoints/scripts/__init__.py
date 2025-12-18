"""
Scripts endpoints package.

Provides API routes for script management including CRUD, generation,
and storyboard operations.
"""

from fastapi import APIRouter

from app.api.v1.endpoints.scripts.crud import router as crud_router

router = APIRouter()

# Include sub-routers
router.include_router(crud_router, tags=["scripts"])

__all__ = ["router"]
