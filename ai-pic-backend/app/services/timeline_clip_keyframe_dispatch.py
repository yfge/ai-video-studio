"""Dispatch Timeline clip keyframe generation tasks."""

from __future__ import annotations

from typing import Any

from app.models.task import Task
from app.models.user import User


def dispatch_timeline_clip_keyframe_task(
    task: Task,
    payload: dict[str, Any],
    current_user: User,
) -> None:
    from app.services.task_worker_timeline_keyframes import (
        timeline_clip_keyframe_generate_task,
    )

    timeline_clip_keyframe_generate_task.delay(task.id, payload, current_user.id)
