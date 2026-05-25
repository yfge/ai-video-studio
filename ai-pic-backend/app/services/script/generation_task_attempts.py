"""Attempt and scoring helpers for async script generation tasks."""

from __future__ import annotations

from typing import Any, Dict

from app.models.script import Episode, Story
from app.services.ai.script_text import build_script_text
from app.services.ai_service import ai_service
from app.services.narrative_quality_gate import enforce_script_quality_gate_with_repair
from app.services.script.content_normalization import normalize_script_content
from app.services.script.sync_generation_payloads import (
    build_agent_run,
    parse_ai_content,
)
from app.services.script_missing_parts import populate_dialogues_and_stage_if_missing
from app.utils.marketing_meta import merge_marketing_meta
from sqlalchemy.orm import Session


async def generate_prepared_script_attempt(
    db: Session,
    *,
    attempt_no: int,
    additional_requirements: str,
    episode: Episode,
    story: Story,
    episode_data: Dict[str, Any],
    story_data: Dict[str, Any],
    request_dict: Dict[str, Any],
    model_id: str | None,
    prefer_provider: str | None,
) -> Dict[str, Any]:
    result = await ai_service.generate_script(
        episode=episode_data,
        story=story_data,
        format_type=request_dict.get("format_type", "screenplay"),
        language=request_dict.get("language", "zh-CN"),
        dialogue_style=request_dict.get("dialogue_style", "natural"),
        scene_detail_level=request_dict.get("scene_detail_level", "medium"),
        template_style=request_dict.get("template_style", "commercial_vertical_drama"),
        target_chars_per_episode=request_dict.get("target_chars_per_episode", 1300),
        quality_threshold=request_dict.get("quality_threshold", 9.0),
        additional_requirements=additional_requirements,
        style_preferences=request_dict.get("style_preferences"),
        model=model_id,
        prefer_provider=prefer_provider,
        temperature=request_dict.get("temperature", 0.7),
    )
    if not result:
        raise RuntimeError("AI剧本生成失败")

    agent_run = {**build_agent_run(result), "attempt": attempt_no}
    ai_content = normalize_script_content(
        parse_ai_content(result),
        format_type=request_dict.get("format_type", "screenplay"),
        language=request_dict.get("language", "zh-CN"),
        default_scenes=episode_data.get("scenes"),
        episode_number=episode.episode_number,
        template_style=request_dict.get("template_style", "commercial_vertical_drama"),
        target_chars_per_episode=request_dict.get("target_chars_per_episode", 1300),
        title=episode.title,
    )
    script_content = ai_content.get("content", "")
    scenes = ai_content.get("scenes", [])
    dialogues_raw = ai_content.get("dialogues", [])
    stage_directions_raw = ai_content.get("stage_directions", [])
    dialogues, stage_directions = populate_dialogues_and_stage_if_missing(
        scenes, dialogues_raw, stage_directions_raw, story=story
    )
    if not dialogues_raw or not stage_directions_raw:
        script_content = build_script_text(
            scenes,
            dialogues,
            stage_directions,
            format_type=request_dict.get("format_type", "screenplay"),
            language=request_dict.get("language", "zh-CN"),
            episode_number=episode.episode_number,
            template_style=request_dict.get(
                "template_style", "commercial_vertical_drama"
            ),
            target_chars_per_episode=request_dict.get("target_chars_per_episode", 1300),
            title=episode.title,
        )
        ai_content["content"] = script_content

    result, ai_content, _quality_gate = await enforce_script_quality_gate_with_repair(
        ai_manager=getattr(ai_service, "ai_manager", None),
        result=result,
        content={
            **ai_content,
            "content": script_content,
            "scenes": scenes,
            "dialogues": dialogues,
            "stage_directions": stage_directions,
        },
        story=story_data,
        story_model=story,
        episode_id=episode.id,
        db=db,
        model=model_id,
        prefer_provider=prefer_provider,
        temperature=request_dict.get("temperature", 0.7),
        lint_threshold=request_dict.get("quality_threshold", 9.0),
        target_chars_per_episode=request_dict.get("target_chars_per_episode", 1300),
    )
    return {
        "result": result,
        "agent_run": {**agent_run, "quality_gate": result.get("quality_gate")},
        "ai_content": ai_content,
        "script_content": ai_content.get("content", ""),
        "scenes": ai_content.get("scenes", []),
        "dialogues": ai_content.get("dialogues", []),
        "stage_directions": ai_content.get("stage_directions", []),
    }


async def score_prepared_script_attempt(
    *,
    generated: Dict[str, Any],
    episode: Episode,
    episode_data: Dict[str, Any],
    story_data: Dict[str, Any],
    marketing_overrides: Dict[str, Any],
    model_id: str | None,
    prefer_provider: str | None,
) -> Dict[str, Any]:
    from app.services.scoring.artifacts import generate_scoring_artifacts

    episode_ctx = dict(episode_data or {})
    episode_ctx.setdefault("episode_number", episode.episode_number)
    episode_ctx.setdefault("title", episode.title)
    episode_ctx.setdefault("summary", episode.summary)
    marketing_defaults = merge_marketing_meta(
        story_data,
        episode_data,
        marketing_overrides,
    )
    return await generate_scoring_artifacts(
        ai_service=ai_service,
        script_content=generated.get("script_content") or "",
        story=story_data,
        episode=episode_ctx,
        scenes=generated.get("scenes") or [],
        dialogues=generated.get("dialogues") or [],
        hook_plan=marketing_defaults.get("hook_plan"),
        prefer_provider=prefer_provider,
        prefer_model=model_id,
    )
