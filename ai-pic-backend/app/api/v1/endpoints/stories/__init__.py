"""
Story endpoints module.

Provides modular story endpoints split by concern:
- crud: Basic CRUD operations
- generation: AI-powered story outline generation
- async_tasks: Background task processing
- novel: Long-form novel export
- characters: Story character listing
- meta: Static metadata endpoints
- readiness: Pre-generation readiness checks
"""

from app.services.ai_service import ai_service
from app.services.story.story_novel_task_processor import (
    process_story_novel_task as process_story_novel_export_task,
)
from fastapi import APIRouter

from .async_tasks import _process_story_generation_task
from .async_tasks import router as async_router
from .characters import router as characters_router
from .crud import router as crud_router
from .generation import router as generation_router
from .meta import router as meta_router
from .novel import router as novel_router
from .novel_adaptation import router as novel_adaptation_router
from .novel_revisions import router as novel_revisions_router
from .readiness import router as readiness_router
from .single_video import router as single_video_router

router = APIRouter()

for sub_router in [
    single_video_router,
    crud_router,
    generation_router,
    async_router,
    novel_router,
    novel_revisions_router,
    novel_adaptation_router,
    characters_router,
    meta_router,
    readiness_router,
]:
    for route in sub_router.routes:
        router.routes.append(route)

__all__ = [
    "router",
    "_process_story_generation_task",
    "process_story_novel_export_task",
    "ai_service",
]
