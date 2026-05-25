from typing import Any, Dict, List, Optional

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
from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.script import Script, Story
from app.models.user import User
from app.schemas.script import ScriptListItemResponse
from app.services.script.story_structure_sync import (
    sync_script_scenes_to_story_structure as _sync_script_scenes_to_story_structure_impl,
)
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session


def _sync_script_scenes_to_story_structure(
    db: Session,
    script: Script,
    *,
    allow_overwrite: bool = False,
) -> Dict[str, int]:
    return _sync_script_scenes_to_story_structure_impl(
        db,
        script,
        allow_overwrite=allow_overwrite,
    )


def _populate_dialogues_and_stage_if_missing(
    scenes: List[Dict[str, Any]],
    dialogues: List[Dict[str, Any]],
    stage_directions: List[Dict[str, Any]],
    *,
    story: Story | None = None,
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Fill missing dialogues/stage_directions without misleading "fake" lines.

    Note: Real dialogue completion should be done at generation time (ScriptLangGraphAgent).
    This function is only a last-resort safeguard to keep downstream pipelines running.
    """
    from app.services.script_missing_parts import (
        populate_dialogues_and_stage_if_missing,
    )

    return populate_dialogues_and_stage_if_missing(
        scenes,
        dialogues,
        stage_directions,
        story=story,
    )


router = APIRouter()
router.include_router(catalog_router)
router.include_router(prompt_router)
router.include_router(generation_queue_router)
router.include_router(generation_sync_router)
router.include_router(create_router)


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


router.include_router(lists_router)
router.include_router(records_router)
router.include_router(regeneration_router)


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
