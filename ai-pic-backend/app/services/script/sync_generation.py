"""Synchronous script generation service."""

from __future__ import annotations

from typing import Any, Dict

from app.core.logging import get_logger
from app.models.script import Script
from app.models.user import User
from app.repositories.scripts_route_repository import ScriptsRouteRepository
from app.schemas.generation_requests import ScriptGenerationRequest
from app.services.ai.script_text import build_script_text
from app.services.ai_service import ai_service
from app.services.narrative_quality_gate import (
    NarrativeQualityGateError,
    enforce_script_quality_gate_with_repair,
)
from app.services.script.content_normalization import normalize_script_content
from app.services.script.context_payloads import (
    build_character_profiles,
    build_episode_data,
    build_story_data,
    collect_previous_episode_summaries,
)
from app.services.script.story_structure_sync import (
    sync_script_scenes_to_story_structure,
)
from app.services.script.sync_generation_payloads import (
    build_agent_run,
    build_generation_params,
    build_marketing_overrides,
    parse_ai_content,
    split_model_provider,
)
from app.services.script_missing_parts import populate_dialogues_and_stage_if_missing
from app.utils.marketing_meta import apply_marketing_overrides, merge_marketing_meta
from fastapi import HTTPException
from sqlalchemy.orm import Session


async def generate_script_sync(
    db: Session,
    request: ScriptGenerationRequest,
    current_user: User,
) -> Script:
    episode = ScriptsRouteRepository(db).get_generation_episode(
        episode_id=request.episode_id,
        current_user=current_user,
    )
    if not episode:
        raise HTTPException(status_code=404, detail="剧集不存在")

    story = episode.story
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")

    previous_episode_summaries = collect_previous_episode_summaries(
        db, story.id, episode.episode_number
    )
    character_profiles = build_character_profiles(story)
    episode_data = build_episode_data(episode)
    story_data = build_story_data(
        story,
        previous_episode_summaries=previous_episode_summaries,
        character_profiles=character_profiles,
    )
    marketing_overrides = build_marketing_overrides(request)
    apply_marketing_overrides(story_data, marketing_overrides)
    apply_marketing_overrides(episode_data, marketing_overrides)

    prefer_provider, model_id = split_model_provider(request.model)
    result = await ai_service.generate_script(
        episode=episode_data,
        story=story_data,
        format_type=request.format_type,
        language=request.language,
        dialogue_style=request.dialogue_style,
        scene_detail_level=request.scene_detail_level,
        template_style=request.template_style,
        target_chars_per_episode=request.target_chars_per_episode,
        quality_threshold=request.quality_threshold,
        additional_requirements=request.additional_requirements,
        style_preferences=request.style_preferences,
        model=model_id,
        prefer_provider=prefer_provider,
        temperature=request.temperature or 0.7,
    )
    if not result:
        raise HTTPException(status_code=500, detail="AI剧本生成失败")

    agent_run = build_agent_run(result)
    ai_content = normalize_script_content(
        parse_ai_content(result),
        format_type=request.format_type,
        language=request.language,
        default_scenes=episode_data.get("scenes"),
        episode_number=episode.episode_number,
        template_style=request.template_style,
        target_chars_per_episode=request.target_chars_per_episode,
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
            format_type=request.format_type,
            language=request.language,
            episode_number=episode.episode_number,
            template_style=request.template_style,
            target_chars_per_episode=request.target_chars_per_episode,
            title=episode.title,
        )
        ai_content["content"] = script_content

    try:
        result, ai_content, _quality_gate = (
            await enforce_script_quality_gate_with_repair(
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
                temperature=request.temperature or 0.7,
                lint_threshold=request.quality_threshold,
                target_chars_per_episode=request.target_chars_per_episode,
            )
        )
    except NarrativeQualityGateError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"剧本质量校验失败: {exc}",
        ) from exc

    if agent_run:
        agent_run = {**agent_run, "quality_gate": result.get("quality_gate")}
    return _persist_generated_script(
        db,
        request,
        episode_title=episode.title,
        result=result,
        ai_content=ai_content,
        story_data=story_data,
        episode_data=episode_data,
        marketing_overrides=marketing_overrides,
        agent_run=agent_run,
    )


def _persist_generated_script(
    db: Session,
    request: ScriptGenerationRequest,
    *,
    episode_title: str,
    result: Dict[str, Any],
    ai_content: Dict[str, Any],
    story_data: Dict[str, Any],
    episode_data: Dict[str, Any],
    marketing_overrides: Dict[str, Any],
    agent_run: Dict[str, Any],
) -> Script:
    script_content = ai_content.get("content", "")
    character_count = len(script_content) if script_content else 0
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
    if agent_run:
        extra_meta = {**(extra_meta or {}), "agent_run": agent_run}
    if episode_data.get("source_novel"):
        extra_meta = {
            **(extra_meta or {}),
            "source_novel": episode_data["source_novel"],
        }

    db_script = Script(
        episode_id=request.episode_id,
        title=f"{episode_title} - 剧本",
        content=script_content,
        scenes=ai_content.get("scenes", []),
        dialogues=ai_content.get("dialogues", []),
        stage_directions=ai_content.get("stage_directions", []),
        format_type=request.format_type,
        language=request.language,
        page_count=max(1, character_count // 2000),
        word_count=len(script_content.split()) if script_content else 0,
        character_count=character_count,
        generation_prompt=result.get("prompt"),
        ai_model=result.get("generation_method"),
        generation_params=build_generation_params(request),
        extra_metadata=extra_meta or None,
        status="draft",
    )
    db.add(db_script)
    db.commit()
    db.refresh(db_script)
    try:
        sync_script_scenes_to_story_structure(db, db_script)
    except Exception:
        logger = get_logger()
        logger.warning("同步规范化场景失败（generate）", exc_info=True)
    return db_script
