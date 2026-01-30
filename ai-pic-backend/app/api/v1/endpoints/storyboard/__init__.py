"""Storyboard API endpoints.

This module provides dedicated endpoints for storyboard operations,
extracted from scripts_legacy.py for better modularity.

Endpoints:
- GET /{script_id}/storyboard - Retrieve storyboard data
- POST /{script_id}/storyboard/preview - Preview generation prompt
- POST /{script_id}/storyboard/generate - Synchronous generation
- POST /{script_id}/storyboard/generate-async - Async generation
- POST /{script_id}/storyboard/update - Save storyboard changes
- POST /{script_id}/storyboard/generate-images - Generate frame images
- POST /{script_id}/storyboard/generate-video - Generate frame videos
"""

from fastapi import APIRouter

from .generation import router as generation_router
from .media import router as media_router
from .retrieval import router as retrieval_router

router = APIRouter()

# Include sub-routers
router.include_router(retrieval_router, tags=["storyboard"])
router.include_router(generation_router, tags=["storyboard"])
router.include_router(media_router, tags=["storyboard"])

__all__ = ["router"]
