"""Small helpers for script regeneration task processing."""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

from app.models.script import Episode, Script
from app.models.task import TaskStatus
from app.repositories.task_repository import TaskRepository
from app.services.narrative_quality_gate import attach_quality_gate_failure_to_task
from sqlalchemy.orm import Session


def allocate_regeneration_scene_budgets(
    episode_data: Dict[str, Any],
    duration_minutes: Optional[float],
    script_id: int,
    logger,
) -> Optional[list[Dict[str, Any]]]:
    if not duration_minutes or duration_minutes <= 0:
        return None
    scenes = episode_data.get("scenes", [])
    if not scenes:
        return None
    from app.services.duration_orchestrator.utils import allocate_scene_budgets

    try:
        scene_budgets, _ = allocate_scene_budgets(
            total_duration_minutes=duration_minutes,
            scenes=scenes,
        )
        logger.info(
            "剧本重新生成: 分配场景预算",
            extra={
                "script_id": script_id,
                "duration_minutes": duration_minutes,
                "scene_count": len(scene_budgets),
            },
        )
        return scene_budgets
    except Exception as exc:
        logger.warning("分配场景预算失败: %s", exc)
        return None


def update_task_status(
    db: Session,
    task_id: int,
    *,
    status: TaskStatus,
    result_file_path: str | None = None,
    error_message: str | None = None,
    quality_gate: Dict[str, Any] | None = None,
) -> None:
    task = TaskRepository(db).get_by_id(task_id)
    if not task:
        return
    if task.status == TaskStatus.CANCELLED:
        # 用户已取消：worker 完成后不得把状态覆盖回 COMPLETED/FAILED
        return
    task.status = status
    if result_file_path is not None:
        task.result_file_path = result_file_path
    if error_message is not None:
        task.error_message = error_message
    if quality_gate is not None:
        attach_quality_gate_failure_to_task(task, quality_gate)
    db.commit()


def next_script_version(old_version: str | None) -> str:
    try:
        major, minor = (old_version or "1.0").split(".")
        return f"{major}.{int(minor) + 1}"
    except (ValueError, AttributeError):
        return "1.1"


def base_script_title(script: Script, episode: Episode) -> str:
    return re.sub(r"\s*\(v[\d.]+\)$", "", script.title or f"剧本 - {episode.title}")
