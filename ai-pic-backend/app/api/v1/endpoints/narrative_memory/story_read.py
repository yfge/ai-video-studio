"""Read-only Story memory endpoints."""

from app.api.v1.endpoints.narrative_memory.dependencies import owned_story
from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.core.middleware import get_current_active_user
from app.models.user import User
from app.repositories.narrative_promotion_repository import NarrativePromotionRepository
from app.schemas.narrative_memory import (
    CharacterMemoryResponse,
    MemorySummaryResponse,
    NarrativeAnchorResponse,
    NarrativeEventResponse,
)
from app.services.narrative_memory.baseline_service import BaselineService
from app.services.narrative_memory.query_service import NarrativeMemoryQueryService
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

router = APIRouter()


@router.get(
    "/business/{story_business_id}/narrative-memory/summary",
    response_model=MemorySummaryResponse,
)
def memory_summary(
    story_business_id: str,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    repo, story = owned_story(db, story_business_id, user)
    return NarrativeMemoryQueryService(repo).summary(story)


@router.get(
    "/business/{story_business_id}/narrative-memory/events",
    response_model=list[NarrativeEventResponse],
)
def list_events(
    story_business_id: str,
    status: str | None = Query(None),
    event_type: str | None = Query(None),
    disclosure: str | None = Query(None),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    repo, story = owned_story(db, story_business_id, user)
    return repo.list_events(
        story.id, status=status, event_type=event_type, disclosure=disclosure
    )


@router.get(
    "/business/{story_business_id}/narrative-memory/characters/{character_business_id}",
    response_model=list[CharacterMemoryResponse],
)
def list_character_memories(
    story_business_id: str,
    character_business_id: str,
    status: str | None = Query(None),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    repo, story = owned_story(db, story_business_id, user)
    if not repo.get_story_character(story.id, character_business_id):
        raise NotFoundError("故事角色", character_business_id)
    return repo.list_character_memories(story.id, character_business_id, status=status)


@router.get(
    "/business/{story_business_id}/narrative-memory/anchors",
    response_model=list[NarrativeAnchorResponse],
)
def list_anchors(
    story_business_id: str,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    repo, story = owned_story(db, story_business_id, user)
    return repo.list_anchors(story.id)


@router.get(
    "/business/{story_business_id}/narrative-memory/anchors/{anchor_business_id}",
    response_model=NarrativeAnchorResponse,
)
def get_anchor(
    story_business_id: str,
    anchor_business_id: str,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    repo, story = owned_story(db, story_business_id, user)
    anchor = repo.get_anchor(story.id, anchor_business_id)
    if not anchor:
        raise NotFoundError("叙事锚点", anchor_business_id)
    return anchor


@router.get("/business/{story_business_id}/narrative-memory/shared-baseline/diff")
def baseline_diff(
    story_business_id: str,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    repo, story = owned_story(db, story_business_id, user)
    service = BaselineService(repo, NarrativePromotionRepository(db))
    return service.diff(story)
