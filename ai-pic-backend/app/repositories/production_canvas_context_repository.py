from __future__ import annotations

from app.models.script import Episode, Story, StoryCharacter
from app.models.user import User
from sqlalchemy.orm import Session


class ProductionCanvasContextRepository:
    """Focused read queries for resolving a canvas prompt to domain entities."""

    def __init__(self, session: Session):
        self.session = session

    def _accessible_stories(self, user: User):
        query = self.session.query(Story).filter(Story.is_deleted.is_(False))
        if not user.is_admin and not user.is_superuser:
            query = query.filter(Story.user_id == user.id)
        return query

    def list_stories(
        self,
        user: User,
        *,
        virtual_ip_id: int | None = None,
        episode_number: int | None = None,
        limit: int = 200,
    ) -> list[Story]:
        query = self._accessible_stories(user)
        if virtual_ip_id is not None:
            query = query.join(
                StoryCharacter, StoryCharacter.story_id == Story.id
            ).filter(
                StoryCharacter.virtual_ip_id == virtual_ip_id,
                StoryCharacter.is_deleted.is_(False),
            )
        if episode_number is not None:
            query = query.join(Episode, Episode.story_id == Story.id).filter(
                Episode.episode_number == episode_number,
                Episode.is_deleted.is_(False),
            )
        return query.order_by(Story.id.desc()).distinct().limit(limit).all()

    def list_story_virtual_ip_ids(self, story_id: int) -> list[int]:
        rows = (
            self.session.query(StoryCharacter.virtual_ip_id)
            .filter(
                StoryCharacter.story_id == story_id,
                StoryCharacter.is_deleted.is_(False),
            )
            .all()
        )
        return sorted({int(row.virtual_ip_id) for row in rows if row.virtual_ip_id})
