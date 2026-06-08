"""Scripts endpoints package."""

from typing import List, Optional

from app.api.v1.endpoints.scripts.audio_storyboard import (
    _process_script_audio_storyboard_task,
)
from app.api.v1.endpoints.scripts.audio_storyboard import (
    router as audio_storyboard_router,
)
from app.api.v1.endpoints.scripts.audio_timeline import (
    _process_script_audio_timeline_task,
)
from app.api.v1.endpoints.scripts.audio_timeline import router as audio_timeline_router
from app.api.v1.endpoints.scripts.dialogue_audio import (
    _process_script_dialogue_audio_task,
)
from app.api.v1.endpoints.scripts.dialogue_audio import router as dialogue_audio_router
from app.api.v1.endpoints.scripts.quality import router as quality_router
from app.api.v1.endpoints.scripts.timeline_pipeline import (
    _process_timeline_pipeline_task,
)
from app.api.v1.endpoints.scripts.timeline_pipeline import (
    router as timeline_pipeline_router,
)
from app.api.v1.endpoints.scripts_catalog import router as catalog_router
from app.api.v1.endpoints.scripts_create import router as create_router
from app.api.v1.endpoints.scripts_generation_queue import (
    router as generation_queue_router,
)
from app.api.v1.endpoints.scripts_generation_sync import (
    router as generation_sync_router,
)
from app.api.v1.endpoints.scripts_lists import get_scripts as _get_scripts
from app.api.v1.endpoints.scripts_lists import router as lists_router
from app.api.v1.endpoints.scripts_prompt import router as prompt_router
from app.api.v1.endpoints.scripts_records import router as records_router
from app.api.v1.endpoints.scripts_regeneration import router as regeneration_router

# Storyboard task processors now live in the storyboard package.
from app.api.v1.endpoints.storyboard import (
    _augment_frames,
    _enforce_storyboard_variety,
    _merge_frames,
    _process_storyboard_generation_task,
    _process_storyboard_image_task,
    _process_storyboard_video_task,
)
from app.api.v1.endpoints.storyboard import router as storyboard_router  # noqa: F401
from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.user import User
from app.schemas.script import ScriptListItemResponse

# Imported for test monkeypatching consistency across endpoint modules.
from app.services.ai_service import ai_service  # noqa: F401
from app.services.script.story_structure_sync import (
    sync_script_scenes_to_story_structure as _sync_script_scenes_to_story_structure,
)
from app.services.script_missing_parts import (
    populate_dialogues_and_stage_if_missing as _populate_dialogues_and_stage_if_missing,
)
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

_ai_service_for_monkeypatch = ai_service

router = APIRouter()
router.include_router(catalog_router)
router.include_router(prompt_router)
router.include_router(generation_queue_router)
router.include_router(generation_sync_router)
router.include_router(create_router)
router.include_router(lists_router)
router.include_router(records_router)
router.include_router(regeneration_router)
router.include_router(quality_router)
router.include_router(dialogue_audio_router)
router.include_router(audio_timeline_router)
router.include_router(timeline_pipeline_router)
router.include_router(audio_storyboard_router)
router.include_router(storyboard_router)


def _process_script_generation_task(task_id: int, request_dict: dict, user_id: int):
    from app.services.script.generation_task_processor import (
        process_script_generation_task,
    )

    return process_script_generation_task(task_id, request_dict, user_id)


def _process_script_regeneration_task(task_id: int, request_dict: dict, user_id: int):
    from app.services.script.regeneration_task_processor import (
        process_script_regeneration_task,
    )

    return process_script_regeneration_task(task_id, request_dict, user_id)


@router.get("", response_model=List[ScriptListItemResponse], include_in_schema=False)
async def get_scripts_no_slash(
    episode_id: Optional[int] = Query(None),
    episode_business_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = Query(None),
    format_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """兼容无尾斜杠的 /api/v1/scripts 请求，避免 307 重定向。"""
    return await _get_scripts(
        episode_id=episode_id,
        episode_business_id=episode_business_id,
        skip=skip,
        limit=limit,
        status=status,
        format_type=format_type,
        current_user=current_user,
        db=db,
    )


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
    "_process_script_regeneration_task",
    "_process_timeline_pipeline_task",
    "_process_storyboard_generation_task",
    "_process_storyboard_image_task",
    "_process_storyboard_video_task",
    "_sync_script_scenes_to_story_structure",
]
