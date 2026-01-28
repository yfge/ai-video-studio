from __future__ import annotations

from typing import Any, Dict, List

from app.models.script import Episode, Story
from app.schemas.generation import EpisodePlanItem
from app.schemas.generation_requests import EpisodeGenerationRequest
from app.services import story_structure_service
from app.services.ai_service import ai_service
from app.utils.marketing_meta import merge_marketing_meta
from pydantic import ValidationError
from sqlalchemy.orm import Session

from .episode_generation_utils import build_step_outline_rows, is_episode_payload_valid
from .episode_summary import build_episode_summary

_KNOWN_EPISODE_KEYS = {
    "episode_number",
    "title",
    "summary",
    "plot_points",
    "character_arcs",
    "conflicts",
    "scene_count",
}


def create_episode_models(
    *,
    db: Session,
    request: EpisodeGenerationRequest,
    story: Story,
    story_data: Dict[str, Any],
    episodes_data: List[Dict[str, Any]],
    result: Dict[str, Any],
    agent_run: Dict[str, Any],
    hook_plan_payload: dict | None,
    ad_snippets_payload: list[dict] | None,
) -> list[Episode]:
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

    created: list[Episode] = []
    for idx, episode_data in enumerate(episodes_data[: request.episode_count]):
        episode_number = episode_data.get("episode_number") or idx + 1
        existing = (
            db.query(Episode)
            .filter(
                Episode.story_id == request.story_id,
                Episode.episode_number == episode_number,
            )
            .first()
        )
        if existing:
            continue

        try:
            EpisodePlanItem.model_validate(episode_data)
        except ValidationError:
            ai_service.logger.warning(
                "Episode schema validation failed; skip persisting",
                extra={"story_id": story.id, "episode_number": episode_number},
            )
            continue

        if not is_episode_payload_valid(episode_data):
            ai_service.logger.warning(
                "Episode validation failed; skip persisting",
                extra={"story_id": story.id, "episode_number": episode_number},
            )
            continue

        extra_meta = {
            k: v for k, v in episode_data.items() if k not in _KNOWN_EPISODE_KEYS
        }
        summary = build_episode_summary(episode_data)
        if summary and not extra_meta.get("episode_summary"):
            extra_meta["episode_summary"] = summary
        extra_metadata = extra_meta or None
        if marketing_defaults:
            extra_metadata = {**(extra_metadata or {}), **marketing_defaults}
        if agent_run:
            extra_metadata = {**(extra_metadata or {}), "agent_run": agent_run}

        db_episode = Episode(
            story_id=request.story_id,
            episode_number=episode_number,
            title=episode_data.get("title", f"第{episode_number}集"),
            summary=episode_data.get("summary"),
            plot_points=episode_data.get("plot_points"),
            character_arcs=episode_data.get("character_arcs"),
            conflicts=episode_data.get("conflicts"),
            duration_minutes=request.episode_duration,
            scene_count=episode_data.get("scene_count"),
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
            },
            extra_metadata=extra_metadata,
            status="draft",
        )
        db.add(db_episode)
        created.append(db_episode)

    return created


def persist_step_outline_beats(
    *,
    db: Session,
    story: Story,
    step_outlines: Dict[str, Any],
    created_episodes: List[Episode],
    agent_run: Dict[str, Any],
    result: Dict[str, Any],
) -> None:
    try:
        treatment = story_structure_service.ensure_auto_treatment(
            db,
            story,
            prompt_snapshot={
                "outline_prompt": result.get("step_outline_prompt"),
                "step_outlines_raw": result.get("step_outlines_raw"),
                "agent_generation_method": agent_run.get("generation_method"),
            },
        )
        episode_id_map = {ep.episode_number: ep.id for ep in created_episodes}
        rows = build_step_outline_rows(
            outlines=step_outlines,
            treatment=treatment,
            story_id=story.id,
            episode_id_map=episode_id_map,
            agent_run=agent_run,
        )
        if rows:
            story_structure_service.bulk_create_step_outlines(db, rows)
    except Exception as exc:
        ai_service.logger.warning(
            "Failed to persist step outlines",
            extra={"error": str(exc), "story_id": story.id},
        )
