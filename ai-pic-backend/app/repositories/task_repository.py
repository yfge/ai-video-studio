from __future__ import annotations

from app.models.task import Task, TaskStatus
from app.repositories.base import BaseRepository
from sqlalchemy.orm import Session


class TaskRepository(BaseRepository[Task]):
    """Repository for Task model operations."""

    def __init__(self, session: Session):
        super().__init__(Task, session)

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
