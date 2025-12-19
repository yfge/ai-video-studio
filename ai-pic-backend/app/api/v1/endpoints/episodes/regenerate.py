"""
Episode regeneration endpoints.

Regenerate AI-generated episode content.
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.script import Story, Episode
from app.models.user import User
from app.schemas.script import EpisodeResponse
from app.services.ai_service import ai_service
from app.utils.json_utils import extract_json_block
from .helpers import (
    get_episode_by_identifier,
    get_story_by_identifier,
    ensure_scenes,
)

router = APIRouter()


def _build_story_data(story: Story) -> Dict[str, Any]:
    """Build story data dict for AI generation."""
    return {
        "title": story.title,
        "genre": story.genre,
        "theme": story.theme,
        "synopsis": story.synopsis,
        "main_conflict": story.main_conflict,
        "resolution": story.resolution,
        "main_characters": story.main_characters,
        "character_relationships": story.character_relationships,
        "world_building": story.world_building,
        "setting_time": story.setting_time,
        "setting_location": story.setting_location,
    }


async def _regenerate_episode_instance(
    *,
    db: Session,
    episode: Episode,
    story: Story,
    current_user: User,
) -> Episode:
    """Shared episode regeneration logic for ID/business_id routes."""
    story_data = _build_story_data(story)
    original_params = episode.generation_params or {}

    result = await ai_service.generate_episodes(
        story=story_data,
        episode_count=1,
        episode_duration=episode.duration_minutes,
        focus_characters=None,
        plot_complexity=original_params.get("plot_complexity", "medium"),
        pacing=original_params.get("pacing", "medium"),
        additional_requirements=f"重新生成第{episode.episode_number}集的内容",
        style_preferences=original_params.get("style_preferences"),
    )

    if not result:
        raise HTTPException(status_code=500, detail="AI剧集重新生成失败")

    agent_run = {}
    if isinstance(result, dict):
        agent_run = {
            "generation_method": result.get("generation_method"),
            "template_used": result.get("template_used"),
            "provider_used": result.get("provider_used"),
            "model_used": result.get("model_used"),
            "usage": result.get("usage"),
            "reasoning": result.get("reasoning"),
        }

    ai_content = (
        result.get("normalized") if isinstance(result, dict) else None
    ) or extract_json_block(result.get("content") if isinstance(result, dict) else None)

    if ai_content:
        episodes_data = ai_content.get("episodes", [])
        if episodes_data:
            episode_data = episodes_data[0]
            scenes, scene_count = ensure_scenes(episode_data)

            new_episode = Episode(
                story_id=episode.story_id,
                story_business_id=getattr(story, "business_id", None),
                episode_number=episode.episode_number,
                title=episode_data.get("title") or episode.title,
                summary=episode_data.get("summary"),
                plot_points=episode_data.get("plot_points"),
                character_arcs=episode_data.get("character_arcs"),
                conflicts=episode_data.get("conflicts"),
                scene_count=scene_count,
                duration_minutes=episode.duration_minutes,
                generation_params=episode.generation_params,
                status=episode.status,
                tags=episode.tags,
                extra_metadata=None,
                generation_prompt=result.get("prompt"),
                ai_model=result.get("generation_method"),
            )

            known_keys = {
                "episode_number",
                "title",
                "summary",
                "plot_points",
                "character_arcs",
                "conflicts",
                "scene_count",
            }
            extra_meta = {
                k: v for k, v in episode_data.items() if k not in known_keys
            } or {}
            if scenes and "scenes" not in extra_meta:
                extra_meta["scenes"] = scenes
            if agent_run:
                extra_meta = {
                    **(extra_meta or {}),
                    "agent_run": agent_run,
                }
            new_episode.extra_metadata = extra_meta or None

            db.add(new_episode)
            db.commit()
            db.refresh(new_episode)

            episode.soft_delete(
                user_id=current_user.id, reason="regenerate superseded"
            )
            db.commit()

            return new_episode

    raise HTTPException(status_code=500, detail="AI生成内容格式错误")


@router.post("/{episode_id}/regenerate", response_model=EpisodeResponse)
async def regenerate_episode(
    episode_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Regenerate episode content by ID."""
    episode = get_episode_by_identifier(db, episode_id, None, current_user)
    story = get_story_by_identifier(db, episode.story_id, None, current_user)
    regenerated = await _regenerate_episode_instance(
        db=db, episode=episode, story=story, current_user=current_user
    )
    return EpisodeResponse.from_orm(regenerated)


@router.post("/business/{episode_business_id}/regenerate", response_model=EpisodeResponse)
async def regenerate_episode_by_business_id(
    episode_business_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Regenerate episode content by business ID."""
    episode = get_episode_by_identifier(db, None, episode_business_id, current_user)
    story = get_story_by_identifier(db, episode.story_id, None, current_user)
    regenerated = await _regenerate_episode_instance(
        db=db, episode=episode, story=story, current_user=current_user
    )
    return EpisodeResponse.from_orm(regenerated)
