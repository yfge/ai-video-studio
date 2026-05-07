"""Data access helpers for the operator workbench."""

from __future__ import annotations

from app.models.script import Episode, Script, Story
from app.models.task import Task, TaskStatus
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload


class WorkbenchRepository:
    def __init__(self, session: Session):
        self.session = session

    def count_tasks_by_status(self, user_id: int) -> dict[TaskStatus, int]:
        rows = (
            self.session.query(Task.status, func.count(Task.id))
            .filter(Task.user_id == user_id, Task.is_deleted.is_(False))
            .group_by(Task.status)
            .all()
        )
        return {status: count for status, count in rows}

    def count_continuable_episodes(self, user_id: int) -> int:
        return (
            self.session.query(func.count(func.distinct(Episode.id)))
            .join(Story, Episode.story_id == Story.id)
            .join(Script, Script.episode_id == Episode.id)
            .filter(
                Story.user_id == user_id,
                Story.is_deleted.is_(False),
                Episode.is_deleted.is_(False),
                Script.is_deleted.is_(False),
            )
            .scalar()
            or 0
        )

    def list_recent_episodes(self, user_id: int, limit: int = 8) -> list[Episode]:
        return (
            self.session.query(Episode)
            .join(Story, Episode.story_id == Story.id)
            .options(joinedload(Episode.story), joinedload(Episode.scripts))
            .filter(
                Story.user_id == user_id,
                Story.is_deleted.is_(False),
                Episode.is_deleted.is_(False),
            )
            .order_by(Episode.updated_at.desc(), Episode.id.desc())
            .limit(limit)
            .all()
        )

    def list_recent_tasks(self, user_id: int, limit: int = 8) -> list[Task]:
        return (
            self.session.query(Task)
            .filter(Task.user_id == user_id, Task.is_deleted.is_(False))
            .order_by(
                func.coalesce(Task.updated_at, Task.created_at).desc(), Task.id.desc()
            )
            .limit(limit)
            .all()
        )
