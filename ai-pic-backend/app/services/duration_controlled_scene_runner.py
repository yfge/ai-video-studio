"""Scene generation phase for duration-controlled dialogue audio."""

from __future__ import annotations

import time
from typing import Any, Callable, Optional

from app.models.script import Episode, Script, Story
from app.models.story_structure import Scene
from app.repositories.audio_timeline_repository import list_active_scene_beats
from app.services.audio.scene_audio_generator import generate_scene_dialogue_audio
from app.services.duration_orchestrator.state import SceneBudget
from sqlalchemy.orm import Session


def _scene_actual_duration(db: Session, scene: Scene) -> float:
    total_duration = 0.0
    for beat in list_active_scene_beats(db, scene.id):
        if beat.duration_seconds:
            total_duration += float(beat.duration_seconds)
    return total_duration


async def generate_scene_audio_with_budgets(
    db: Session,
    *,
    story: Story,
    episode: Episode,
    script: Script,
    scenes: list[Scene],
    scene_budgets: list[SceneBudget],
    total_duration_minutes: int,
    tts_model: str,
    overwrite_beats: bool,
    timing_model: Optional[str],
    progress_callback: Optional[Callable[[str], None]],
    logger: Any,
    log_prefix: str,
) -> dict[str, Any]:
    budget_map = {budget.scene_number: budget for budget in scene_budgets}

    if progress_callback:
        progress_callback(f"Phase 2/3: 生成 {len(scenes)} 个场景对白音轨...")

    phase_start = time.time()
    generation_results: list[dict[str, Any]] = []
    total_actual_duration = 0.0
    scene_timings: list[int] = []

    for idx, scene in enumerate(scenes, start=1):
        scene_start = time.time()
        scene_number = getattr(scene, "scene_number", idx)
        budget = budget_map.get(scene_number)

        target_duration = None
        if budget:
            target_duration = budget.target_duration_seconds
        if not target_duration:
            target_duration = getattr(scene, "estimated_duration_seconds", None)
        if not target_duration:
            target_duration = (total_duration_minutes * 60) // len(scenes)

        if progress_callback:
            progress_callback(
                f"场景 {idx}/{len(scenes)}: 生成中 (目标 {target_duration:.0f}s)"
            )

        logger.info(
            f"{log_prefix}: 开始生成场景 {scene_number}",
            extra={
                "phase": "scene_generation",
                "episode_id": episode.id,
                "scene_number": scene_number,
                "scene_index": idx,
                "scene_total": len(scenes),
                "target_duration_seconds": target_duration,
            },
        )

        try:
            await generate_scene_dialogue_audio(
                db,
                story=story,
                episode=episode,
                script=script,
                scene=scene,
                tts_model=tts_model,
                overwrite_beats=overwrite_beats,
                timing_model=timing_model,
                target_duration_seconds=target_duration,
            )

            actual_duration = _scene_actual_duration(db, scene)
            total_actual_duration += actual_duration
            scene_duration_ms = int((time.time() - scene_start) * 1000)
            deviation = actual_duration - target_duration
            deviation_pct = (
                (deviation / target_duration * 100) if target_duration else 0
            )

            if budget:
                budget.actual_duration_seconds = actual_duration

            generation_results.append(
                {
                    "scene_number": scene_number,
                    "target_duration": target_duration,
                    "actual_duration": actual_duration,
                    "deviation_seconds": round(deviation, 2),
                    "deviation_percent": round(deviation_pct, 1),
                    "success": True,
                    "generation_ms": scene_duration_ms,
                }
            )
            scene_timings.append(scene_duration_ms)

            logger.info(
                f"{log_prefix}: 场景 {scene_number} 生成完成",
                extra={
                    "phase": "scene_generation",
                    "episode_id": episode.id,
                    "scene_number": scene_number,
                    "target_duration": target_duration,
                    "actual_duration": actual_duration,
                    "deviation_seconds": round(deviation, 2),
                    "deviation_percent": round(deviation_pct, 1),
                    "generation_ms": scene_duration_ms,
                },
            )

            if progress_callback:
                progress_callback(
                    f"场景 {idx}/{len(scenes)}: 完成 "
                    f"({actual_duration:.1f}s, 偏差 {deviation_pct:+.0f}%)"
                )

        except Exception as exc:
            scene_duration_ms = int((time.time() - scene_start) * 1000)
            logger.exception(
                f"{log_prefix}: 场景 {scene_number} 生成失败",
                extra={
                    "phase": "scene_generation",
                    "episode_id": episode.id,
                    "scene_number": scene_number,
                    "error": str(exc),
                    "generation_ms": scene_duration_ms,
                },
            )
            generation_results.append(
                {
                    "scene_number": scene_number,
                    "target_duration": target_duration,
                    "error": str(exc),
                    "success": False,
                    "generation_ms": scene_duration_ms,
                }
            )
            if progress_callback:
                progress_callback(f"场景 {idx}/{len(scenes)}: 失败 - {str(exc)[:50]}")

    return {
        "generation_results": generation_results,
        "total_actual_duration": total_actual_duration,
        "scene_timings": scene_timings,
        "phase_duration": time.time() - phase_start,
    }
