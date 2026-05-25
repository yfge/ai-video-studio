"""Persistence helpers for async script generation tasks."""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.core.logging import get_logger
from app.models.script import Episode, Script, Story
from app.services.script.production_metadata import merge_production_pipeline_metadata
from app.services.script.production_pipeline import run_auto_timeline_placeholders
from app.services.script.story_structure_sync import (
    sync_script_scenes_to_story_structure,
)
from app.utils.marketing_meta import merge_marketing_meta
from sqlalchemy.orm import Session


def create_generated_script(
    db: Session,
    *,
    request_dict: Dict[str, Any],
    episode: Episode,
    generated: Dict[str, Any],
    extra_meta: Dict[str, Any],
) -> Script:
    script_content = generated.get("script_content") or ""
    character_count = len(script_content) if script_content else 0
    result = generated["result"]
    script = Script(
        episode_id=request_dict.get("episode_id"),
        title=f"{episode.title} - 剧本",
        content=script_content,
        scenes=generated.get("scenes") or [],
        dialogues=generated.get("dialogues") or [],
        stage_directions=generated.get("stage_directions") or [],
        format_type=request_dict.get("format_type", "screenplay"),
        language=request_dict.get("language", "zh-CN"),
        page_count=max(1, character_count // 2000),
        word_count=len(script_content.split()) if script_content else 0,
        character_count=character_count,
        generation_prompt=result.get("prompt"),
        ai_model=result.get("generation_method"),
        generation_params={
            key: request_dict.get(key)
            for key in [
                "generation_mode",
                "auto_timeline_pipeline",
                "dialogue_style",
                "scene_detail_level",
                "template_style",
                "target_chars_per_episode",
                "quality_threshold",
                "market_region",
                "micro_genre",
                "hook_plan",
                "twist_density",
                "cliffhanger_plan",
                "ad_snippets",
                "additional_requirements",
                "style_preferences",
                "model",
                "temperature",
            ]
        },
        extra_metadata=extra_meta or None,
        status="draft",
    )
    db.add(script)
    db.commit()
    db.refresh(script)
    try:
        sync_script_scenes_to_story_structure(db, script)
    except Exception:
        logger = get_logger()
        logger.warning("同步规范化场景失败（generate-async）", exc_info=True)
    return script


def build_generation_extra_metadata(
    *,
    generated: Dict[str, Any],
    story_data: Dict[str, Any],
    episode_data: Dict[str, Any],
    marketing_overrides: Dict[str, Any],
    generation_mode: str,
    production_meta: Dict[str, Any],
    scoring_artifacts: Optional[Dict[str, Any]],
    auto_timeline_pipeline: bool,
) -> Dict[str, Any]:
    ai_content = generated["ai_content"]
    extra_meta = {
        key: value
        for key, value in ai_content.items()
        if key not in {"content", "scenes", "dialogues", "stage_directions", "metadata"}
    }
    marketing_defaults = merge_marketing_meta(
        story_data, episode_data, marketing_overrides
    )
    if marketing_defaults:
        extra_meta = {**extra_meta, **marketing_defaults}
    agent_run = generated.get("agent_run") or {}
    if generation_mode != "production" and scoring_artifacts:
        extra_meta = {**(extra_meta or {}), "scoring": scoring_artifacts}
        agent_run = {**agent_run, "scoring": scoring_artifacts}
    if generation_mode == "production":
        production_meta["auto_timeline_pipeline"] = {
            "enabled": bool(auto_timeline_pipeline),
            "status": "pending" if auto_timeline_pipeline else "skipped",
        }
        extra_meta = {
            **(extra_meta or {}),
            "production_pipeline": production_meta,
            "scoring": scoring_artifacts,
        }
        agent_run = {
            **agent_run,
            "production_pipeline": production_meta,
            "scoring": scoring_artifacts,
        }
    if agent_run:
        extra_meta = {**(extra_meta or {}), "agent_run": agent_run}
    return extra_meta


def run_auto_timeline_pipeline(
    db: Session,
    *,
    story: Story,
    episode: Episode,
    script: Script,
    production_meta: Dict[str, Any],
    scoring_artifacts: Optional[Dict[str, Any]],
    user_id: int,
) -> Dict[str, Any]:
    import anyio

    async def _run_auto_timeline():
        return await run_auto_timeline_placeholders(
            db,
            story=story,
            episode=episode,
            script=script,
            hook_schedule=production_meta.get("hook_schedule") or {},
            scoring=scoring_artifacts,
            user_id=user_id,
        )

    return anyio.run(_run_auto_timeline)


def merge_generated_production_metadata(
    db: Session,
    script: Script,
    *,
    production_meta: Dict[str, Any],
    scoring_artifacts: Optional[Dict[str, Any]],
) -> None:
    merge_production_pipeline_metadata(
        db,
        script,
        production_meta=production_meta,
        scoring_artifacts=scoring_artifacts,
    )
