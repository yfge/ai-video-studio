"""
Episode endpoints module.

Provides modular episode endpoints split by concern:
- crud: Basic CRUD operations
- generation: AI-powered episode generation
- regenerate: Episode content regeneration
- async_tasks: Background task processing

The combined router aggregates all sub-routers for mounting in the API.
"""

from fastapi import APIRouter

# Re-export the background task processor for Celery
from .async_tasks import process_episode_generation_task
from .async_tasks import router as async_router
from .crud import router as crud_router
from .generation import router as generation_router

# Re-export helpers for other modules that may need them
from .helpers import (
    build_outline_rows,
    build_stub_episodes_from_outlines,
    ensure_scenes,
    get_episode_by_identifier,
    get_story_by_identifier,
    is_episode_payload_valid,
    not_deleted,
    parse_step_outlines,
    persist_story_outlines,
    update_task_progress,
)
from .regenerate import router as regenerate_router

# Combined router that includes all episode endpoints
# Note: We aggregate all routes from sub-routers into a single router.
# The parent api.py mounts this at /episodes prefix.
router = APIRouter()

# Include sub-routers - routes are defined with their full paths in each module
# Using include_router with prefix="" merges routes directly
for sub_router in [crud_router, generation_router, regenerate_router, async_router]:
    for route in sub_router.routes:
        router.routes.append(route)

__all__ = [
    "router",
    "process_episode_generation_task",
    # Helper exports
    "not_deleted",
    "get_episode_by_identifier",
    "get_story_by_identifier",
    "is_episode_payload_valid",
    "parse_step_outlines",
    "persist_story_outlines",
    "build_outline_rows",
    "build_stub_episodes_from_outlines",
    "update_task_progress",
    "ensure_scenes",
]
