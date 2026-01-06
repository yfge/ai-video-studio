"""
Story endpoints module.

Provides modular story endpoints split by concern:
- crud: Basic CRUD operations
- generation: AI-powered story outline generation
- async_tasks: Background task processing
- characters: Story character listing
- meta: Static metadata endpoints
"""

from fastapi import APIRouter

from .async_tasks import _process_story_generation_task, router as async_router
from .characters import router as characters_router
from .crud import router as crud_router
from .generation import router as generation_router
from .meta import router as meta_router

router = APIRouter()

for sub_router in [crud_router, generation_router, async_router, characters_router, meta_router]:
    for route in sub_router.routes:
        router.routes.append(route)

__all__ = ["router", "_process_story_generation_task"]
