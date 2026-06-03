from __future__ import annotations

from typing import Any, Dict

from app.models.script import Episode, Story
from app.repositories.episode_repository import find_episode_by_story_number
from app.schemas.generation import EpisodePlanItem
from app.schemas.generation_requests import EpisodeGenerationRequest
from app.services.episode.episode_generation_utils import is_episode_payload_valid
from app.services.episode.episode_scene_normalization import ensure_scenes
from app.services.episode.episode_summary import build_episode_summary
from app.utils.marketing_meta import merge_marketing_meta
from pydantic import ValidationError
from sqlalchemy.orm import Session

_KNOWN_EPISODE_KEYS = {
    "episode_number",
    "title",
    "summary",
    "plot_points",
    "character_arcs",
    "conflicts",
    "scene_count",
}


def _marketing_payloads(
    request: EpisodeGenerationRequest,
) -> tuple[dict | None, list[dict] | None]:
    hook_plan_payload = (
        request.hook_plan.model_dump()
        if hasattr(request.hook_plan, "model_dump")
        else request.hook_plan
    )
    ad_snippets_payload = (
        [
            item.model_dump() if hasattr(item, "model_dump") else item
            for item in request.ad_snippets
        ]
        if request.ad_snippets
        else None
    )
    return hook_plan_payload, ad_snippets_payload


def persist_episode_record(
    *,
    db: Session,
    request: EpisodeGenerationRequest,
    story: Story,
    story_data: Dict[str, Any],
    episode_data: Dict[str, Any],
    fallback_number: int,
    result: Dict[str, Any],
    agent_run: Dict[str, Any],
    progress_fn,
) -> tuple[Episode | None, bool]:
    episode_number = episode_data.get("episode_number") or fallback_number
    progress_fn(f"生成第{episode_number}集：校验中")
    existing = find_episode_by_story_number(
        db,
        story_id=story.id,
        episode_number=episode_number,
    )
    if existing:
        return existing, False

    try:
        EpisodePlanItem.model_validate(episode_data)
    except ValidationError as exc:
        progress_fn(f"生成第{episode_number}集：schema校验失败")
        raise RuntimeError(
            f"生成第{episode_number}集失败：输出不符合 EpisodePlanItem schema"
        ) from exc
    if not is_episode_payload_valid(episode_data):
        progress_fn(f"生成第{episode_number}集：内容校验失败")
        raise RuntimeError(f"生成第{episode_number}集失败：输出不符合最小内容约束")

    hook_plan_payload, ad_snippets_payload = _marketing_payloads(request)
    marketing_defaults = merge_marketing_meta(
        story_data,
        {
            "market_region": request.market_region,
            "micro_genre": request.micro_genre,
            "hook_plan": hook_plan_payload,
            "twist_density": request.twist_density,
            "cliffhanger_plan": request.cliffhanger_plan,
            "ad_snippets": ad_snippets_payload,
        },
    )
    scenes, scene_count = ensure_scenes(episode_data)
    extra_meta = {k: v for k, v in episode_data.items() if k not in _KNOWN_EPISODE_KEYS}
    summary = build_episode_summary(episode_data)
    if summary and not extra_meta.get("episode_summary"):
        extra_meta["episode_summary"] = summary
    if scenes and "scenes" not in extra_meta:
        extra_meta["scenes"] = scenes
    if marketing_defaults:
        extra_meta = {**extra_meta, **marketing_defaults}

    db_episode = Episode(
        story_id=story.id,
        episode_number=episode_number,
        title=episode_data.get("title", f"第{episode_number}集"),
        summary=episode_data.get("summary"),
        plot_points=episode_data.get("plot_points"),
        character_arcs=episode_data.get("character_arcs"),
        conflicts=episode_data.get("conflicts"),
        duration_minutes=request.episode_duration,
        scene_count=scene_count,
        generation_prompt=result.get("prompt") or result.get("step_outline_prompt"),
        ai_model=result.get("generation_method") or result.get("model_used"),
        generation_params={
            "focus_characters": request.focus_characters,
            "plot_complexity": request.plot_complexity,
            "pacing": request.pacing,
            "market_region": request.market_region,
            "micro_genre": request.micro_genre,
            "hook_plan": hook_plan_payload,
            "twist_density": request.twist_density,
            "cliffhanger_plan": request.cliffhanger_plan,
            "ad_snippets": ad_snippets_payload,
            "additional_requirements": request.additional_requirements,
            "style_preferences": request.style_preferences,
            "model": request.model,
            "temperature": request.temperature,
        },
        extra_metadata={**(extra_meta or {}), "agent_run": agent_run},
        status="draft",
    )
    db.add(db_episode)
    db.commit()
    db.refresh(db_episode)
    progress_fn(f"生成第{episode_number}集：已落库")
    return db_episode, True
