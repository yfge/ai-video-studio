from __future__ import annotations

from app.models.task import Task
from app.repositories.base import BaseRepository
from sqlalchemy.orm import Session


class TaskRepository(BaseRepository[Task]):
    """Repository for Task model operations."""

    def __init__(self, session: Session):
        super().__init__(Task, session)
