"""Narrative memory API routers."""

from fastapi import APIRouter

from .dramatic_state import router as dramatic_state_router
from .promotion import router as promotion_router
from .story_read import router as story_read_router
from .story_write import router as story_write_router

story_router = APIRouter()
story_router.include_router(story_read_router)
story_router.include_router(story_write_router)

__all__ = [
    "dramatic_state_router",
    "promotion_router",
    "story_router",
]
