"""Storyboard retrieval endpoints.

GET operations for storyboard data and prompt preview.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import get_logger
from app.core.middleware import get_current_active_user
from app.models.script import Episode, Script, Story
from app.models.user import User
from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate
from app.services.ai.storyboard_utils import build_storyboard_context
from app.utils.marketing_meta import merge_marketing_meta

from .utils import get_script_with_auth

router = APIRouter()
logger = get_logger()


@router.get("/{script_id}/storyboard")
async def get_storyboard(
    script_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Retrieve storyboard data for a script.

    Returns frames, metadata (version, updated_at), and plan if available.
    """
    script = get_script_with_auth(db, script_id, current_user)

    storyboard = (
        (script.extra_metadata or {}).get("storyboard")
        if script.extra_metadata
        else None
    )

    # Log retrieval for debugging
    try:
        frames = (storyboard or {}).get("frames") or []
        first_url = None
        if isinstance(frames, list) and frames:
            first = frames[0] or {}
            if isinstance(first, dict):
                first_url = first.get("image_url")
        logger.info(
            f"Storyboard GET | script_id={script_id} "
            f"frames={len(frames)} first_image={bool(first_url)}"
        )
    except Exception:
        pass

    data = dict(storyboard or {"frames": []})
    meta = dict(data.get("meta") or {})

    if script.storyboard_version is not None:
        meta.setdefault("version", script.storyboard_version)
    if script.storyboard_updated_at:
        meta.setdefault("updated_at", script.storyboard_updated_at.isoformat())

    data["meta"] = meta
    if script.storyboard_plan:
        data["plan"] = script.storyboard_plan

    return {"success": True, "data": data}


@router.post("/{script_id}/storyboard/preview")
async def preview_storyboard_prompt(
    script_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Preview the AI prompt that would be used for storyboard generation.

    Does not actually generate storyboard - useful for debugging prompts.
    """
    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="剧本不存在")

    episode = script.episode
    story = episode.story if episode else None

    # Merge marketing metadata
    story_marketing = merge_marketing_meta(
        (
            story.extra_metadata
            if story and isinstance(story.extra_metadata, dict)
            else {}
        ),
        (
            story.generation_params
            if story and isinstance(story.generation_params, dict)
            else {}
        ),
    )
    episode_marketing = merge_marketing_meta(
        (
            episode.extra_metadata
            if episode and isinstance(episode.extra_metadata, dict)
            else {}
        ),
        (
            episode.generation_params
            if episode and isinstance(episode.generation_params, dict)
            else {}
        ),
    )

    scenes = script.scenes or []
    scene_indices = list(range(1, len(scenes) + 1))

    script_data = {
        "content": script.content,
        "scenes": scenes,
        "dialogues": script.dialogues,
        "stage_directions": script.stage_directions,
        "scene_indices": scene_indices,
        "episode": (
            {
                "episode_number": episode.episode_number if episode else None,
                "title": episode.title if episode else None,
                "summary": episode.summary if episode else None,
                "duration_minutes": episode.duration_minutes if episode else None,
                "scene_count": episode.scene_count if episode else None,
                **episode_marketing,
            }
            if episode
            else None
        ),
        "story": (
            {
                "title": story.title if story else None,
                "genre": story.genre if story else None,
                "theme": story.theme if story else None,
                "setting_time": story.setting_time if story else None,
                "setting_location": story.setting_location if story else None,
                "world_building": story.world_building if story else None,
                "main_characters": story.main_characters if story else None,
                **story_marketing,
            }
            if story
            else None
        ),
    }

    context_text = build_storyboard_context(script_data)
    prompt = prompt_manager.render_prompt(
        PromptTemplate.STORYBOARD_GENERATION.value,
        {
            "frames_per_scene": 7,
            "max_frames": None,
            "context_text": context_text,
            "style_preferences": [],
            "additional_requirements": None,
        },
    )

    return {"success": True, "data": {"prompt": prompt}}
