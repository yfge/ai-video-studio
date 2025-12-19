from __future__ import annotations

from typing import Iterable, List, Optional

from sqlalchemy.orm import Session

from app.models.video_generation_task import (
    VideoGenerationTask,
    VideoGenerationTaskStatus,
)
from app.repositories.base import BaseRepository


class VideoGenerationTaskRepository(BaseRepository[VideoGenerationTask]):
    def __init__(self, session: Session):
        super().__init__(VideoGenerationTask, session)

    def list_pending(self, limit: int = 50) -> List[VideoGenerationTask]:
        statuses = [
            VideoGenerationTaskStatus.SUBMITTED,
            VideoGenerationTaskStatus.PROCESSING,
        ]
        return (
            self.session.query(self.model)
            .filter(
                self.model.is_deleted.is_(False),
                self.model.status.in_(statuses),
            )
            .order_by(self.model.id.asc())
            .limit(limit)
            .all()
        )

    def list_by_task_id(self, task_id: int) -> List[VideoGenerationTask]:
        return (
            self.session.query(self.model)
            .filter(self.model.is_deleted.is_(False), self.model.task_id == task_id)
            .all()
        )

    def count_by_task_id(
        self,
        task_id: int,
        statuses: Optional[Iterable[VideoGenerationTaskStatus]] = None,
    ) -> int:
        query = self.session.query(self.model).filter(
            self.model.is_deleted.is_(False),
            self.model.task_id == task_id,
        )
        if statuses is not None:
            query = query.filter(self.model.status.in_(list(statuses)))
        return query.count()
