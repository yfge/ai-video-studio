"""
Scripts endpoints package.

Provides API routes for script management including CRUD, generation,
and storyboard operations.

Note: During refactoring, legacy routes from scripts_legacy.py are
temporarily re-exported here. They will be migrated in subsequent phases.
"""

from fastapi import APIRouter

# Import legacy router and task helpers for storyboard and other unmigrated endpoints.
from app.api.v1.endpoints.scripts_legacy import (  # noqa: F401
    _augment_frames,
    _enforce_storyboard_variety,
    _merge_frames,
    _populate_dialogues_and_stage_if_missing,
    _process_script_audio_storyboard_task,
    _process_script_audio_timeline_task,
    _process_script_dialogue_audio_task,
    _process_script_generation_task,
    _process_storyboard_generation_task,
    _process_storyboard_image_task,
    _process_storyboard_video_task,
    _sync_script_scenes_to_story_structure,
    router as legacy_router,
)

# New refactored routers will be added here as migration progresses
# from app.api.v1.endpoints.scripts.crud import router as crud_router
# from app.api.v1.endpoints.scripts.generation import router as generation_router

# For now, use the legacy router to maintain all functionality
# Once all endpoints are migrated, we'll switch to using the new routers
router = legacy_router

__all__ = [
    "router",
    "_augment_frames",
    "_enforce_storyboard_variety",
    "_merge_frames",
    "_populate_dialogues_and_stage_if_missing",
    "_process_script_audio_storyboard_task",
    "_process_script_audio_timeline_task",
    "_process_script_dialogue_audio_task",
    "_process_script_generation_task",
    "_process_storyboard_generation_task",
    "_process_storyboard_image_task",
    "_process_storyboard_video_task",
    "_sync_script_scenes_to_story_structure",
]
