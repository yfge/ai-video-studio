"""Dispatch grid storyboard sheet tasks."""

from __future__ import annotations

from typing import Any

from app.models.user import User


def dispatch_grid_storyboard_sheet_task(
    task,
    payload: dict[str, Any],
    current_user: User,
) -> None:
    from app.services.task_worker_grid_storyboard import (
        grid_storyboard_sheet_generate_task,
    )

    grid_storyboard_sheet_generate_task.delay(task.id, payload, current_user.id)
