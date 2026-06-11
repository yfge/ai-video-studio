"""User-facing task control (cancel) on top of the task status machine.

Cancellation is DB-state best-effort: celery task ids are not persisted, so a
PROCESSING worker may still run to completion; status writers that respect the
CANCELLED guard (script generation path) will not resurrect a cancelled task.
"""

from __future__ import annotations

from app.models.task import TASK_STATUS_TRANSITIONS, Task, TaskStatus
from app.models.user import User
from app.repositories.task_repository import TaskRepository
from fastapi import HTTPException, status
from sqlalchemy.orm import Session


class TaskControlService:
    def __init__(self, db: Session):
        self.db = db
        self.tasks = TaskRepository(db)

    def cancel_task(self, task_id: int, current_user: User) -> Task:
        task = self.tasks.get_by_id(task_id)
        if (
            task is None
            or getattr(task, "is_deleted", False)
            or task.user_id != current_user.id
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在",
            )
        allowed = TASK_STATUS_TRANSITIONS.get(task.status, set())
        if TaskStatus.CANCELLED not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"当前状态 {task.status.value} 不允许取消",
            )
        task.status = TaskStatus.CANCELLED
        task.error_message = "已被用户取消"
        self.db.commit()
        self.db.refresh(task)
        return task
