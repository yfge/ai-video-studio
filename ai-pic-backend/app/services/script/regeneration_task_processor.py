"""Script regeneration Celery task processor."""

from __future__ import annotations

from typing import Any, Dict

import anyio
from app.core.logging import get_logger
from app.models.script import Episode, Script, Story
from app.models.task import TaskStatus
from app.repositories.scripts_route_repository import ScriptsRouteRepository
from app.services.narrative_quality_gate import NarrativeQualityGateError
from app.services.script.context_payloads import (
    build_character_profiles,
    build_episode_data,
    build_story_data,
    collect_previous_episode_summaries,
)
from app.services.script.regeneration_generation import build_regenerated_script_payload
from app.services.script.regeneration_task_helpers import (
    allocate_regeneration_scene_budgets,
    base_script_title,
    next_script_version,
    update_task_status,
)
from app.services.script.story_structure_sync import (
    sync_script_scenes_to_story_structure,
)
from app.utils.marketing_meta import apply_marketing_overrides, merge_marketing_meta
from sqlalchemy.orm import Session


def process_script_regeneration_task(
    task_id: int, request_dict: dict, user_id: int
) -> None:
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        logger = get_logger("script_regenerate_task")
        update_task_status(db, task_id, status=TaskStatus.PROCESSING)
        script = ScriptsRouteRepository(db).get_regeneration_script(
            script_id=request_dict.get("script_id"),
            user_id=user_id,
        )
        if not script:
            raise RuntimeError("剧本不存在")

        episode, story = _get_script_context(script)
        episode_data, story_data, marketing_overrides = _build_context_payloads(
            db, episode, story, request_dict
        )
        scene_budgets = allocate_regeneration_scene_budgets(
            episode_data, request_dict.get("duration_minutes"), script.id, logger
        )

        async def _run_regeneration_payload():
            return await build_regenerated_script_payload(
                db,
                script=script,
                episode=episode,
                story=story,
                episode_data=episode_data,
                story_data=story_data,
                request_dict=request_dict,
                marketing_overrides=marketing_overrides,
                scene_budgets=scene_budgets,
            )

        payload = anyio.run(_run_regeneration_payload)
        new_script = _persist_regenerated_script(
            db,
            script=script,
            episode=episode,
            story_data=story_data,
            episode_data=episode_data,
            marketing_overrides=marketing_overrides,
            request_dict=request_dict,
            payload=payload,
        )
        script.soft_delete(
            user_id=user_id,
            reason=f"regenerated_to_script_{new_script.id}",
        )
        db.commit()
        logger.info(
            "剧本重新生成: 创建新版本并软删除旧版本",
            extra={
                "old_script_id": script.id,
                "new_script_id": new_script.id,
                "old_version": script.version or "1.0",
                "new_version": new_script.version,
            },
        )
        try:
            sync_script_scenes_to_story_structure(db, new_script)
        except Exception:
            logger.warning("同步规范化场景失败（regenerate-async）", exc_info=True)
        update_task_status(
            db,
            task_id,
            status=TaskStatus.COMPLETED,
            result_file_path=f"script:{new_script.id}",
        )
    except Exception as exc:
        update_task_status(
            db,
            task_id,
            status=TaskStatus.FAILED,
            error_message=str(exc),
            quality_gate=(
                exc.quality_gate if isinstance(exc, NarrativeQualityGateError) else None
            ),
        )
    finally:
        db.close()


def _build_context_payloads(
    db: Session,
    episode: Episode,
    story: Story,
    request_dict: Dict[str, Any],
) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
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
    return episode_data, story_data, marketing_overrides


def _persist_regenerated_script(
    db: Session,
    *,
    script: Script,
    episode: Episode,
    story_data: Dict[str, Any],
    episode_data: Dict[str, Any],
    marketing_overrides: Dict[str, Any],
    request_dict: Dict[str, Any],
    payload: Dict[str, Any],
) -> Script:
    new_version = next_script_version(script.version)
    new_meta = dict(script.extra_metadata or {})
    new_meta["parent_script_id"] = script.id
    new_meta["parent_script_business_id"] = script.business_id
    new_meta["regenerated_from_version"] = script.version or "1.0"
    marketing_defaults = merge_marketing_meta(
        story_data, episode_data, marketing_overrides
    )
    if marketing_defaults:
        new_meta = {**new_meta, **marketing_defaults}
    if payload.get("scoring"):
        new_meta = {**new_meta, "scoring": payload["scoring"]}
    if payload.get("agent_run"):
        new_meta["agent_run"] = payload["agent_run"]

    script_content = payload.get("script_content") or ""
    new_script = Script(
        episode_id=script.episode_id,
        episode_business_id=script.episode_business_id,
        title=f"{base_script_title(script, episode)} (v{new_version})",
        content=script_content,
        scenes=payload.get("scenes") or [],
        dialogues=payload.get("dialogues") or [],
        stage_directions=payload.get("stage_directions") or [],
        format_type=request_dict.get("format_type") or script.format_type,
        language=request_dict.get("language") or script.language,
        generation_prompt=payload["result"].get("prompt"),
        ai_model=payload["result"].get("generation_method"),
        generation_params=request_dict,
        status="draft",
        version=new_version,
        tags=script.tags,
        extra_metadata=new_meta,
        word_count=len(script_content.split()) if script_content else 0,
        character_count=len(script_content) if script_content else 0,
        page_count=max(1, len(script_content) // 2000) if script_content else 1,
    )
    db.add(new_script)
    db.commit()
    db.refresh(new_script)
    return new_script


def _get_script_context(script: Script) -> tuple[Episode, Story]:
    episode = script.episode
    if not episode or getattr(episode, "is_deleted", False):
        raise RuntimeError("剧集不存在")
    story = episode.story
    if not story or getattr(story, "is_deleted", False):
        raise RuntimeError("故事不存在")
    return episode, story
