from __future__ import annotations

from typing import Optional

from app.models.script import Episode, Story
from app.models.user import User
from sqlalchemy.orm import Session


def find_episode_by_story_number(
    db: Session,
    *,
    story_id: int,
    episode_number: int,
) -> Episode | None:
    return (
        db.query(Episode)
        .filter(
            Episode.story_id == story_id,
            Episode.episode_number == episode_number,
        )
        .first()
    )


def find_accessible_episode(
    db: Session,
    *,
    episode_id: Optional[int],
    episode_business_id: Optional[str],
    current_user: User,
) -> Episode | None:
    query = (
        db.query(Episode)
        .join(Story, Episode.story_id == Story.id)
        .filter(Episode.is_deleted.is_(False), Story.is_deleted.is_(False))
    )
    if episode_business_id:
        query = query.filter(Episode.business_id == episode_business_id)
    elif episode_id:
        query = query.filter(Episode.id == episode_id)
    else:
        return None
    if not current_user.is_admin and not current_user.is_superuser:
        query = query.filter(Story.user_id == current_user.id)
    return query.first()


def find_accessible_story(
    db: Session,
    *,
    story_id: Optional[int],
    story_business_id: Optional[str],
    current_user: User,
) -> Story | None:
    query = db.query(Story).filter(Story.is_deleted.is_(False))
    if story_business_id:
        query = query.filter(Story.business_id == story_business_id)
    elif story_id:
        query = query.filter(Story.id == story_id)
    else:
        return None
    if not current_user.is_admin and not current_user.is_superuser:
        query = query.filter(Story.user_id == current_user.id)
    return query.first()
