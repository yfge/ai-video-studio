from __future__ import annotations

from app.models.script import Episode, Story, StoryCharacter
from app.models.story_novel_export import StoryNovelChapter, StoryNovelExport
from app.models.story_structure import StoryTreatment
from app.models.task import Task
from app.models.user import User
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload, selectinload


class StoryNovelRepository:
    """All database reads for the story-novel adaptation aggregate."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def accessible_story(self, business_id: str, user: User) -> Story | None:
        query = self.db.query(Story).filter(
            Story.is_deleted.is_(False), Story.business_id == business_id
        )
        if not (user.is_admin or user.is_superuser):
            query = query.filter(Story.user_id == user.id)
        return query.first()

    def accessible_story_by_id(self, story_id: int, user: User) -> Story | None:
        query = self.db.query(Story).filter(
            Story.is_deleted.is_(False), Story.id == story_id
        )
        if not (user.is_admin or user.is_superuser):
            query = query.filter(Story.user_id == user.id)
        return query.first()

    def accessible_revision(
        self,
        business_id: str,
        user: User,
        *,
        with_chapters: bool = True,
        for_update: bool = False,
    ) -> StoryNovelExport | None:
        query = (
            self.db.query(StoryNovelExport)
            .join(Story, StoryNovelExport.story_id == Story.id)
            .filter(
                StoryNovelExport.business_id == business_id,
                StoryNovelExport.is_deleted.is_(False),
                Story.is_deleted.is_(False),
            )
        )
        if with_chapters:
            query = query.options(selectinload(StoryNovelExport.chapters))
        if not (user.is_admin or user.is_superuser):
            query = query.filter(Story.user_id == user.id)
        if for_update:
            query = query.with_for_update()
        return query.first()

    def list_revisions(self, story_id: int, user: User) -> list[StoryNovelExport]:
        query = (
            self.db.query(StoryNovelExport)
            .filter(
                StoryNovelExport.story_id == story_id,
                StoryNovelExport.is_deleted.is_(False),
            )
            .options(selectinload(StoryNovelExport.chapters))
        )
        if not (user.is_admin or user.is_superuser):
            query = query.filter(StoryNovelExport.user_id == user.id)
        return query.order_by(StoryNovelExport.revision_number.desc()).all()

    def list_exports(
        self, story_id: int, user: User, limit: int
    ) -> list[StoryNovelExport]:
        query = self.db.query(StoryNovelExport).filter(
            StoryNovelExport.story_id == story_id,
            StoryNovelExport.is_deleted.is_(False),
        )
        if not (user.is_admin or user.is_superuser):
            query = query.filter(StoryNovelExport.user_id == user.id)
        return query.order_by(StoryNovelExport.id.desc()).limit(limit).all()

    def export_by_task(self, task_id: int, user: User) -> StoryNovelExport | None:
        query = self.db.query(StoryNovelExport).filter(
            StoryNovelExport.task_id == task_id,
            StoryNovelExport.is_deleted.is_(False),
        )
        if not (user.is_admin or user.is_superuser):
            query = query.filter(StoryNovelExport.user_id == user.id)
        return query.order_by(StoryNovelExport.id.desc()).first()

    def revision_for_task_or_target(
        self, task_id: int, target_business_id: str | None, user_id: int
    ) -> StoryNovelExport | None:
        query = self.db.query(StoryNovelExport).filter(
            StoryNovelExport.is_deleted.is_(False),
            StoryNovelExport.user_id == user_id,
        )
        row = query.filter(StoryNovelExport.task_id == task_id).first()
        if row or not target_business_id:
            return row
        return query.filter(StoryNovelExport.business_id == target_business_id).first()

    def next_revision_number(self, story_id: int) -> int:
        value = (
            self.db.query(func.max(StoryNovelExport.revision_number))
            .filter(StoryNovelExport.story_id == story_id)
            .scalar()
        )
        return max(0, int(value or 0)) + 1

    def chapter(self, revision_id: int, business_id: str) -> StoryNovelChapter | None:
        return (
            self.db.query(StoryNovelChapter)
            .filter(
                StoryNovelChapter.novel_export_id == revision_id,
                StoryNovelChapter.business_id == business_id,
                StoryNovelChapter.is_deleted.is_(False),
            )
            .first()
        )

    def chapters_from_position(
        self, revision_id: int, position: int
    ) -> list[StoryNovelChapter]:
        return (
            self.db.query(StoryNovelChapter)
            .filter(
                StoryNovelChapter.novel_export_id == revision_id,
                StoryNovelChapter.position >= position,
                StoryNovelChapter.is_deleted.is_(False),
            )
            .order_by(StoryNovelChapter.position)
            .all()
        )

    def task(self, task_id: int) -> Task | None:
        return self.db.query(Task).filter(Task.id == task_id).first()

    def accessible_task(self, task_id: int, user: User) -> Task | None:
        query = self.db.query(Task).filter(Task.id == task_id)
        if not (user.is_admin or user.is_superuser):
            query = query.filter(Task.user_id == user.id)
        return query.first()

    def user(self, user_id: int) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def episodes_by_ids(self, ids: list[int]) -> list[Episode]:
        if not ids:
            return []
        return self.db.query(Episode).filter(Episode.id.in_(ids)).all()

    def story_episodes(self, story_id: int, limit: int) -> list[Episode]:
        return (
            self.db.query(Episode)
            .filter(Episode.story_id == story_id, Episode.is_deleted.is_(False))
            .order_by(Episode.episode_number.asc())
            .limit(limit)
            .all()
        )

    def story_characters(self, story_id: int, limit: int) -> list[StoryCharacter]:
        return (
            self.db.query(StoryCharacter)
            .filter(
                StoryCharacter.story_id == story_id,
                StoryCharacter.is_deleted.is_(False),
            )
            .options(joinedload(StoryCharacter.virtual_ip))
            .limit(limit)
            .all()
        )

    def next_treatment_revision_number(self, story_id: int) -> int:
        value = (
            self.db.query(func.max(StoryTreatment.revision_number))
            .filter(StoryTreatment.story_id == story_id)
            .scalar()
        )
        return int(value or 0) + 1
