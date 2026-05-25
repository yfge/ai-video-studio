"""Context helpers for async script generation tasks."""

from __future__ import annotations

from typing import Any, Dict

from app.models.script import Episode, Story
from app.repositories.scripts_route_repository import ScriptsRouteRepository
from app.services.script.context_payloads import (
    build_character_profiles,
    build_episode_data,
    build_story_data,
    collect_previous_episode_summaries,
)
from app.utils.marketing_meta import apply_marketing_overrides
from sqlalchemy.orm import Session


def build_generation_task_context(
    db: Session,
    request_dict: Dict[str, Any],
    user_id: int,
) -> tuple[Episode, Story, Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    episode = ScriptsRouteRepository(db).get_task_generation_episode(
        episode_id=request_dict.get("episode_id"),
        user_id=user_id,
    )
    if not episode:
        raise RuntimeError("剧集不存在")
    story = episode.story
    if not story:
        raise RuntimeError("故事不存在")

    previous_episode_summaries = collect_previous_episode_summaries(
        db, story.id, episode.episode_number
    )
    episode_data = build_episode_data(episode)
    story_data = build_story_data(
        story,
        previous_episode_summaries=previous_episode_summaries,
        character_profiles=build_character_profiles(story),
    )
    marketing_overrides = {
        "market_region": request_dict.get("market_region"),
        "micro_genre": request_dict.get("micro_genre"),
        "hook_plan": request_dict.get("hook_plan"),
        "twist_density": request_dict.get("twist_density"),
        "cliffhanger_plan": request_dict.get("cliffhanger_plan"),
        "ad_snippets": request_dict.get("ad_snippets"),
    }
    apply_marketing_overrides(story_data, marketing_overrides)
    apply_marketing_overrides(episode_data, marketing_overrides)
    return episode, story, episode_data, story_data, marketing_overrides
