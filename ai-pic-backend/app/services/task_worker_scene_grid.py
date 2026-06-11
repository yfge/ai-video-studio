"""Celery task registrations for scene grid storyboard generation."""

from __future__ import annotations

from typing import Any, Dict

import anyio

from app.core.celery_app import celery_app


@celery_app.task(name="tasks.scene_grid_sheet_generate")
def scene_grid_sheet_generate_task(
    task_id: int, payload: Dict[str, Any], user_id: int | None = None
) -> None:
    """异步生成场景宫格分镜大图。"""
    from app.core.database import get_task_db
    from app.services.storyboard.scene_grid import process_scene_grid_sheet_task

    with get_task_db() as db:
        anyio.run(process_scene_grid_sheet_task, db, task_id, payload, user_id)


@celery_app.task(name="tasks.scene_grid_video_generate")
def scene_grid_video_generate_task(
    task_id: int, payload: Dict[str, Any], user_id: int | None = None
) -> None:
    """异步从宫格分镜图生成连续成片（Seedance 等参考图视频模型）。"""
    from app.core.database import get_task_db
    from app.services.storyboard.scene_grid import process_scene_grid_video_task

    with get_task_db() as db:
        anyio.run(process_scene_grid_video_task, db, task_id, payload, user_id)
