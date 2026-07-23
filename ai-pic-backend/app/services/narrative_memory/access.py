"""Ownership and optimistic-concurrency helpers."""

from app.core.exceptions import ConflictError, NotFoundError
from app.models.script import Story
from app.models.user import User
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository


def require_story(
    repo: NarrativeMemoryRepository, story_business_id: str, user: User
) -> Story:
    story = repo.get_owned_story(story_business_id, user)
    if not story:
        raise NotFoundError.story(story_business_id)
    return story


def require_version(entity, expected_version: int) -> None:
    actual = int(entity.version or 1)
    if actual != expected_version:
        raise ConflictError(
            "内容已被其他窗口更新",
            context={"expected_version": expected_version, "actual_version": actual},
        )
