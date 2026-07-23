"""Small constructors shared by narrative memory routes."""

from app.models.user import User
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.repositories.narrative_promotion_repository import NarrativePromotionRepository
from app.services.narrative_memory.access import require_story
from sqlalchemy.orm import Session


def owned_story(db: Session, story_business_id: str, user: User):
    repo = NarrativeMemoryRepository(db)
    return repo, require_story(repo, story_business_id, user)


def promotion_repos(db: Session):
    return NarrativeMemoryRepository(db), NarrativePromotionRepository(db)
