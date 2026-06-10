"""List in-flight generation tasks attached to one timeline's clips."""

from __future__ import annotations

import json
from typing import Any

from app.models.task import Task
from app.models.user import User
from app.repositories.task_repository import TaskRepository
from app.repositories.timeline_repository import TimelineRepository
from app.schemas.timeline_clip_tasks import (
    TimelineClipTaskItem,
    TimelineClipTaskListResponse,
)
from app.services.timeline_clip_video_rework_helpers import story_owner_filter
from fastapi import HTTPException, status
from sqlalchemy.orm import Session


def _clip_id_from_parameters(task: Task) -> str | None:
    if not task.parameters:
        return None
    try:
        loaded: Any = json.loads(task.parameters)
    except (TypeError, ValueError):
        return None
    if not isinstance(loaded, dict):
        return None
    clip_id = loaded.get("clip_id")
    return clip_id if isinstance(clip_id, str) and clip_id.strip() else None


class TimelineClipTaskStatusService:
    def __init__(self, db: Session):
        self.timelines = TimelineRepository(db)
        self.tasks = TaskRepository(db)

    def list_active_clip_tasks(
        self, timeline_id: int, current_user: User
    ) -> TimelineClipTaskListResponse:
        timeline = self.timelines.get_accessible(
            timeline_id=timeline_id,
            user_id=story_owner_filter(current_user),
        )
        if timeline is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="timeline not found",
            )
        tasks = self.tasks.list_active_for_target(
            user_id=current_user.id,
            target_business_id=timeline.business_id,
        )
        items = [
            TimelineClipTaskItem(
                task_id=task.id,
                clip_id=_clip_id_from_parameters(task),
                status=(
                    task.status.value
                    if hasattr(task.status, "value")
                    else str(task.status)
                ),
                task_type=(
                    task.task_type.value
                    if hasattr(task.task_type, "value")
                    else str(task.task_type)
                ),
                title=task.title,
            )
            for task in tasks
        ]
        return TimelineClipTaskListResponse(items=items)
