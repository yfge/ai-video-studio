"""Storyboard API endpoints.

This module provides dedicated endpoints for storyboard operations,
extracted from the old monolithic scripts endpoint for better modularity.

Endpoints:
- GET /{script_id}/storyboard - Retrieve storyboard data
- POST /{script_id}/storyboard/preview - Preview generation prompt
- POST /{script_id}/storyboard/generate - Synchronous generation
- POST /{script_id}/storyboard/generate-async - Async generation
- POST /{script_id}/storyboard/update - Save storyboard changes
- POST /{script_id}/storyboard/generate-images - Generate frame images
- POST /{script_id}/storyboard/generate-video - Generate frame videos
- POST /{script_id}/storyboard/scene-grid/generate - Generate scene grid sheet
- POST /{script_id}/storyboard/scene-grid/video - Generate grid-based video
- GET /{script_id}/storyboard/scene-grid - List generated scene grids
"""

from fastapi import APIRouter

from .generation import router as generation_router
from .media import router as media_router
from .retrieval import router as retrieval_router
from .scene_grid import router as scene_grid_router

router = APIRouter()

# Include sub-routers
router.include_router(retrieval_router, tags=["storyboard"])
router.include_router(generation_router, tags=["storyboard"])
router.include_router(media_router, tags=["storyboard"])
router.include_router(scene_grid_router, tags=["storyboard"])

# Re-export frame utilities used by tests and other modules
from .frame_utils import (  # noqa: E402, F401
    _augment_frames,
    _enforce_storyboard_variety,
    _merge_frames,
)

# Re-export task processors for Celery workers
from .image_task_processor import _process_storyboard_image_task  # noqa: E402, F401
from .task_processors import (  # noqa: E402, F401
    _process_storyboard_generation_task,
    _process_storyboard_video_task,
)

__all__ = [
    "router",
    "_process_storyboard_generation_task",
    "_process_storyboard_image_task",
    "_process_storyboard_video_task",
    "_augment_frames",
    "_enforce_storyboard_variety",
    "_merge_frames",
]
