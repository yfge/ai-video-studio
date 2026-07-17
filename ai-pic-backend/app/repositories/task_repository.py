from __future__ import annotations

from app.models.task import Task, TaskStatus, TaskType
from app.repositories.base import BaseRepository
from sqlalchemy.orm import Session


class TaskRepository(BaseRepository[Task]):
    """Repository for Task model operations."""

    def __init__(self, session: Session):
        super().__init__(Task, session)

    def get_user_task(self, *, task_id: int, user_id: int) -> Task | None:
        """Get one non-deleted task owned by the user."""
        return (
            self.session.query(Task)
            .filter(
                Task.id == task_id,
                Task.user_id == user_id,
                Task.is_deleted.is_(False),
            )
            .first()
        )

    def get_canvas_run_task(self, business_id: str) -> Task | None:
        return (
            self.session.query(Task)
            .filter(
                Task.business_id == business_id,
                Task.is_deleted.is_(False),
            )
            .first()
        )

    def list_for_user(
        self,
        *,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        status_filter: TaskStatus | None = None,
        task_type: TaskType | None = None,
    ) -> tuple[list[Task], int]:
        """List the user's non-deleted tasks with filters and total count."""
        query = self.session.query(Task).filter(
            Task.user_id == user_id,
            Task.is_deleted.is_(False),
        )
        if status_filter:
            query = query.filter(Task.status == status_filter)
        if task_type:
            query = query.filter(Task.task_type == task_type)
        total = query.count()
        tasks = query.order_by(Task.id.desc()).offset(skip).limit(limit).all()
        return tasks, total

    def list_active_for_target(
        self, *, user_id: int, target_business_id: str
    ) -> list[Task]:
        """List the user's pending/processing tasks bound to one target."""
        return (
            self.session.query(Task)
            .filter(
                Task.user_id == user_id,
                Task.target_business_id == target_business_id,
                Task.status.in_([TaskStatus.PENDING, TaskStatus.PROCESSING]),
            )
            .order_by(Task.id.desc())
            .all()
        )

    def list_active_for_target_any_user(
        self,
        *,
        target_business_id: str,
        task_type: TaskType | None = None,
    ) -> list[Task]:
        """List active tasks for a shared target regardless of task owner."""
        query = self.session.query(Task).filter(
            Task.target_business_id == target_business_id,
            Task.status.in_([TaskStatus.PENDING, TaskStatus.PROCESSING]),
            Task.is_deleted.is_(False),
        )
        if task_type is not None:
            query = query.filter(Task.task_type == task_type)
        return query.order_by(Task.id.desc()).all()

    def list_active_by_request_fingerprint(
        self,
        *,
        user_id: int,
        task_type: TaskType,
        request_fingerprint: str,
    ) -> list[Task]:
        """List active tasks whose JSON payload may contain one fingerprint.

        The caller must decode and compare the full value. The text predicate is
        only a narrow database-side candidate filter for the legacy JSON column.
        """
        fingerprint_token = f'"request_fingerprint": "{request_fingerprint}"'
        return (
            self.session.query(Task)
            .filter(
                Task.user_id == user_id,
                Task.task_type == task_type,
                Task.status.in_([TaskStatus.PENDING, TaskStatus.PROCESSING]),
                Task.is_deleted.is_(False),
                Task.parameters.contains(fingerprint_token),
            )
            .order_by(Task.id.desc())
            .all()
        )
