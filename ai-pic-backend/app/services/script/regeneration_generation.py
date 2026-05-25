"""Content generation helpers for script regeneration tasks."""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.core.logging import get_logger
from app.models.script import Episode, Script, Story
from app.services.ai.script_text import build_script_text
from app.services.ai_service import ai_service
from app.services.narrative_quality_gate import enforce_script_quality_gate_with_repair
from app.services.script.content_normalization import normalize_script_content
from app.services.script.sync_generation_payloads import (
    build_agent_run,
    parse_ai_content,
    split_model_provider,
)
from app.services.script_missing_parts import populate_dialogues_and_stage_if_missing
from app.utils.marketing_meta import merge_marketing_meta
from sqlalchemy.orm import Session


async def build_regenerated_script_payload(
    db: Session,
    *,
    script: Script,
    episode: Episode,
    story: Story,
    episode_data: Dict[str, Any],
    story_data: Dict[str, Any],
    request_dict: Dict[str, Any],
    marketing_overrides: Dict[str, Any],
    scene_budgets: Optional[list[Dict[str, Any]]],
) -> Dict[str, Any]:
    prefer_provider, model_id = split_model_provider(request_dict.get("model"))
    result = await ai_service.generate_script(
        episode=episode_data,
        story=story_data,
        format_type=request_dict.get("format_type") or script.format_type,
        language=request_dict.get("language") or script.language,
        dialogue_style=request_dict.get("dialogue_style", "natural"),
        scene_detail_level=request_dict.get("scene_detail_level", "medium"),
        template_style=request_dict.get("template_style", "commercial_vertical_drama"),
        target_chars_per_episode=request_dict.get("target_chars_per_episode", 1300),
        quality_threshold=request_dict.get("quality_threshold", 9.0),
        additional_requirements=request_dict.get("additional_requirements"),
        style_preferences=request_dict.get("style_preferences"),
        model=model_id,
        prefer_provider=prefer_provider,
        temperature=request_dict.get("temperature", 0.7),
        scene_budgets=scene_budgets,
    )
    if not result:
        raise RuntimeError("AI剧本重新生成失败")

    agent_run = build_agent_run(result)
    ai_content = normalize_script_content(
        parse_ai_content(result),
        format_type=request_dict.get("format_type") or script.format_type,
        language=request_dict.get("language") or script.language,
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
            format_type=request_dict.get("format_type") or script.format_type,
            language=request_dict.get("language") or script.language,
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
    if agent_run:
        agent_run = {**agent_run, "quality_gate": result.get("quality_gate")}

    script_content = ai_content.get("content", "")
    scenes = ai_content.get("scenes", [])
    dialogues = ai_content.get("dialogues", [])
    scoring_artifacts = await _build_regeneration_scoring(
        ai_service=ai_service,
        script_content=script_content,
        story_data=story_data,
        episode=episode,
        episode_data=episode_data,
        scenes=scenes,
        dialogues=dialogues,
        marketing_overrides=marketing_overrides,
        prefer_provider=prefer_provider,
        model_id=model_id,
    )
    if scoring_artifacts and agent_run:
        agent_run = {**agent_run, "scoring": scoring_artifacts}
    return {
        "result": result,
        "ai_content": ai_content,
        "script_content": script_content,
        "scenes": scenes,
        "dialogues": dialogues,
        "stage_directions": ai_content.get("stage_directions", []),
        "agent_run": agent_run,
        "scoring": scoring_artifacts,
    }


async def _build_regeneration_scoring(
    *,
    ai_service,
    script_content: str,
    story_data: Dict[str, Any],
    episode: Episode,
    episode_data: Dict[str, Any],
    scenes: list[Dict[str, Any]],
    dialogues: list[Dict[str, Any]],
    marketing_overrides: Dict[str, Any],
    prefer_provider: str | None,
    model_id: str | None,
) -> Dict[str, Any] | None:
    marketing_defaults = merge_marketing_meta(
        story_data,
        episode_data,
        marketing_overrides,
    )
    if not marketing_defaults:
        return None
    try:
        from app.services.scoring.artifacts import generate_scoring_artifacts

        episode_ctx = dict(episode_data or {})
        episode_ctx.setdefault("episode_number", episode.episode_number)
        episode_ctx.setdefault("title", episode.title)
        episode_ctx.setdefault("summary", episode.summary)
        return await generate_scoring_artifacts(
            ai_service=ai_service,
            script_content=script_content,
            story=story_data,
            episode=episode_ctx,
            scenes=scenes,
            dialogues=dialogues,
            hook_plan=marketing_defaults.get("hook_plan"),
            prefer_provider=prefer_provider,
            prefer_model=model_id,
        )
    except Exception:
        logger = get_logger("script_regenerate_task")
        logger.warning("生成评分/投流表失败（regenerate-async）", exc_info=True)
        return None
