"""Repository queries for story character visual context."""

from __future__ import annotations

from app.models.episode_character import EpisodeCharacter
from app.models.script import Story, StoryCharacter
from app.models.virtual_ip import VirtualIP
from sqlalchemy.orm import Session, joinedload


class StoryCharacterVisualRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_story_with_character_images(self, story_id: int) -> Story | None:
        return (
            self.session.query(Story)
            .options(
                joinedload(Story.story_characters)
                .joinedload(StoryCharacter.virtual_ip)
                .joinedload(VirtualIP.images)
            )
            .filter(Story.id == story_id, Story.is_deleted.is_(False))
            .first()
        )

    def list_episode_characters_with_images(
        self,
        episode_id: int,
    ) -> list[EpisodeCharacter]:
        return (
            self.session.query(EpisodeCharacter)
            .options(
                joinedload(EpisodeCharacter.virtual_ip).joinedload(VirtualIP.images)
            )
            .filter(
                EpisodeCharacter.episode_id == episode_id,
                EpisodeCharacter.is_deleted.is_(False),
            )
            .order_by(EpisodeCharacter.importance.desc(), EpisodeCharacter.id.asc())
            .all()
        )
