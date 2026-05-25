"""Dispatch provider-backed Timeline clip video rework tasks."""

from __future__ import annotations

from typing import Any

from app.models.task import Task
from app.models.user import User
from app.services.task_worker_timeline_rework import (
    timeline_clip_rework_video_generate_task,
)


def dispatch_timeline_clip_video_rework_task(
    task: Task,
    payload: dict[str, Any],
    current_user: User,
) -> None:
    timeline_clip_rework_video_generate_task.delay(task.id, payload, current_user.id)
