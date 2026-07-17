"""Script generation Celery task processor."""

from __future__ import annotations

from typing import Any, Dict, Optional

import anyio
from app.core.logging import get_logger
from app.models.task import TaskStatus
from app.services.narrative_quality_gate import NarrativeQualityGateError
from app.services.script.generation_task_attempts import (
    generate_prepared_script_attempt,
    score_prepared_script_attempt,
)
from app.services.script.generation_task_context import build_generation_task_context
from app.services.script.generation_task_persistence import (
    build_generation_extra_metadata,
    create_generated_script,
    merge_generated_production_metadata,
    run_auto_timeline_pipeline,
)
from app.services.script.production_pipeline import run_production_script_generation
from app.services.script.regeneration_task_helpers import update_task_status
from app.services.script.sync_generation_payloads import split_model_provider
from app.utils.marketing_meta import merge_marketing_meta


def process_script_generation_task(
    task_id: int, request_dict: dict, user_id: int
) -> None:
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        logger = get_logger("storyboard_image_task")
        update_task_status(db, task_id, status=TaskStatus.PROCESSING)
        episode, story, episode_data, story_data, marketing_overrides = (
            build_generation_task_context(db, request_dict, user_id)
        )
        prefer_provider, model_id = split_model_provider(request_dict.get("model"))
        generation_mode = request_dict.get("generation_mode") or "production"
        auto_timeline_pipeline = request_dict.get("auto_timeline_pipeline")
        if auto_timeline_pipeline is None:
            auto_timeline_pipeline = generation_mode == "production"

        async def _generate_prepared_attempt(
            attempt_no: int, additional_requirements: str
        ) -> Dict[str, Any]:
            return await generate_prepared_script_attempt(
                db,
                attempt_no=attempt_no,
                additional_requirements=additional_requirements,
                episode=episode,
                story=story,
                episode_data=episode_data,
                story_data=story_data,
                request_dict=request_dict,
                model_id=model_id,
                prefer_provider=prefer_provider,
            )

        async def _score_prepared_attempt(
            generated: Dict[str, Any],
        ) -> Dict[str, Any]:
            return await score_prepared_script_attempt(
                generated=generated,
                episode=episode,
                episode_data=episode_data,
                story_data=story_data,
                marketing_overrides=marketing_overrides,
                model_id=model_id,
                prefer_provider=prefer_provider,
                requirements=request_dict.get("additional_requirements"),
            )

        generated, production_meta, scoring_artifacts = _run_generation_mode(
            generation_mode,
            request_dict,
            story_data,
            episode_data,
            marketing_overrides,
            _generate_prepared_attempt,
            _score_prepared_attempt,
        )
        extra_meta = build_generation_extra_metadata(
            generated=generated,
            story_data=story_data,
            episode_data=episode_data,
            marketing_overrides=marketing_overrides,
            generation_mode=generation_mode,
            production_meta=production_meta,
            scoring_artifacts=scoring_artifacts,
            auto_timeline_pipeline=bool(auto_timeline_pipeline),
        )
        script = create_generated_script(
            db,
            request_dict=request_dict,
            episode=episode,
            generated=generated,
            extra_meta=extra_meta,
        )
        if generation_mode == "production" and production_meta:
            _apply_auto_timeline_pipeline(
                db,
                story=story,
                episode=episode,
                script=script,
                production_meta=production_meta,
                scoring_artifacts=scoring_artifacts,
                auto_timeline_pipeline=bool(auto_timeline_pipeline),
                user_id=user_id,
                logger=logger,
            )
        update_task_status(
            db,
            task_id,
            status=TaskStatus.COMPLETED,
            result_file_path=f"script:{script.id}",
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


def _run_generation_mode(
    generation_mode: str,
    request_dict: Dict[str, Any],
    story_data: Dict[str, Any],
    episode_data: Dict[str, Any],
    marketing_overrides: Dict[str, Any],
    generate_attempt,
    score_attempt,
) -> tuple[Dict[str, Any], Dict[str, Any], Optional[Dict[str, Any]]]:
    if generation_mode == "production":

        async def _run_production():
            return await run_production_script_generation(
                story=story_data,
                episode=episode_data,
                marketing_overrides=marketing_overrides,
                base_additional_requirements=request_dict.get(
                    "additional_requirements"
                ),
                generate_attempt=generate_attempt,
                score_attempt=score_attempt,
            )

        production_result = anyio.run(_run_production)
        selected = production_result.selected
        generated = {
            **selected,
            "agent_run": {
                **(selected.get("agent_run") or {}),
                "generation_mode": "production",
                "scoring": selected.get("scoring"),
                "production_pipeline": production_result.metadata(),
            },
        }
        return generated, production_result.metadata(), selected.get("scoring")

    generated = anyio.run(
        generate_attempt,
        1,
        request_dict.get("additional_requirements") or "",
    )
    marketing_defaults = merge_marketing_meta(
        story_data,
        episode_data,
        marketing_overrides,
    )
    scoring_artifacts = (
        _run_standard_scoring(generated, score_attempt) if marketing_defaults else None
    )
    if scoring_artifacts:
        generated["agent_run"] = {
            **(generated.get("agent_run") or {}),
            "scoring": scoring_artifacts,
        }
    return generated, {}, scoring_artifacts


def _run_standard_scoring(generated: Dict[str, Any], score_attempt):
    try:
        return anyio.run(score_attempt, generated)
    except Exception:
        logger = get_logger("storyboard_image_task")
        logger.warning("生成评分/投流表失败（generate-async）", exc_info=True)
        generated["agent_run"] = {
            **(generated.get("agent_run") or {}),
            "scoring_error": "failed_to_generate",
        }
        return None


def _apply_auto_timeline_pipeline(
    db,
    *,
    story,
    episode,
    script,
    production_meta: Dict[str, Any],
    scoring_artifacts: Optional[Dict[str, Any]],
    auto_timeline_pipeline: bool,
    user_id: int,
    logger,
) -> None:
    if auto_timeline_pipeline:
        try:
            auto_result = run_auto_timeline_pipeline(
                db,
                story=story,
                episode=episode,
                script=script,
                production_meta=production_meta,
                scoring_artifacts=scoring_artifacts,
                user_id=user_id,
            )
            production_meta["auto_timeline_pipeline"] = {
                "enabled": True,
                **auto_result,
            }
        except Exception as exc:
            logger.warning(
                "生产级自动时间轴/分镜占位失败（generate-async）",
                exc_info=True,
            )
            production_meta["auto_timeline_pipeline"] = {
                "enabled": True,
                "status": "failed",
                "error": str(exc),
            }
    merge_generated_production_metadata(
        db,
        script,
        production_meta=production_meta,
        scoring_artifacts=scoring_artifacts,
    )
