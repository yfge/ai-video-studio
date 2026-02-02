"""
Readiness check endpoints for story/episode generation.

Provides synchronous validation to check if all prerequisites
are met before starting generation tasks.
"""

from __future__ import annotations

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.script import Episode, Story
from app.models.user import User
from app.schemas.readiness import QuickFixRequest, QuickFixResponse, ReadinessResult
from app.services.readiness import (
    EpisodeReadinessChecker,
    StoryQuickFixService,
    StoryReadinessChecker,
)
from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from .helpers import get_story_by_identifier

router = APIRouter()


def _get_story(story_id: int, db: Session, user: User) -> Story:
    """Retrieve story by ID with ownership check."""
    story = (
        db.query(Story)
        .filter(Story.id == story_id, Story.is_deleted.is_(False))
        .first()
    )
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    if story.user_id and story.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this story")
    return story


def _get_episode(episode_id: int, story_id: int, db: Session) -> Episode:
    """Retrieve episode by ID with story match check."""
    episode = (
        db.query(Episode)
        .filter(
            Episode.id == episode_id,
            Episode.story_id == story_id,
            Episode.is_deleted.is_(False),
        )
        .first()
    )
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    return episode


@router.post("/{story_id}/readiness-check", response_model=ReadinessResult)
async def check_story_readiness(
    story_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ReadinessResult:
    """
    Check if story is ready for episode generation.

    Validates:
    - Required fields (title, genre)
    - Character linkages and portrait images
    - Marketing metadata (for short_drama format)
    - Content quality (synopsis, main_conflict, setting)

    Returns a ReadinessResult with all check details.
    """
    story = _get_story(story_id, db, current_user)
    checker = StoryReadinessChecker(db)
    return checker.check(story)


@router.post("/business/{story_business_id}/readiness-check", response_model=ReadinessResult)
async def check_story_readiness_by_business_id(
    story_business_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ReadinessResult:
    """Check story readiness by business_id."""
    story = get_story_by_identifier(db, None, story_business_id, current_user)
    checker = StoryReadinessChecker(db)
    return checker.check(story)


@router.post(
    "/{story_id}/episodes/{episode_id}/readiness-check",
    response_model=ReadinessResult,
)
async def check_episode_readiness(
    story_id: int,
    episode_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ReadinessResult:
    """
    Check if episode is ready for script generation.

    Extends story readiness checks with episode-specific validations:
    - Episode exists and is not deleted
    - Episode belongs to the target story
    - Previous episodes have scripts (for continuity)

    Returns a ReadinessResult with all check details.
    """
    story = _get_story(story_id, db, current_user)
    episode = _get_episode(episode_id, story_id, db)
    checker = EpisodeReadinessChecker(db)
    return checker.check(story, episode)


@router.post("/{story_id}/quick-fix", response_model=QuickFixResponse)
async def quick_fix_story(
    story_id: int,
    request: QuickFixRequest = Body(default_factory=QuickFixRequest),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> QuickFixResponse:
    """
    Auto-fix missing story fields using AI generation.

    Automatically fills in missing fields like:
    - synopsis (if title/genre/premise are available)
    - main_conflict (if synopsis/premise available)
    - setting_time (based on genre/synopsis)
    - world_building (based on genre/setting/synopsis)

    Set dry_run=true to preview what would be fixed without applying changes.

    Returns:
        QuickFixResponse with fixes applied, initial/final readiness, and improvement stats.
    """
    story = _get_story(story_id, db, current_user)
    service = StoryQuickFixService(db)
    return await service.fix_story(story, dry_run=request.dry_run)


@router.post("/business/{story_business_id}/quick-fix", response_model=QuickFixResponse)
async def quick_fix_story_by_business_id(
    story_business_id: str,
    request: QuickFixRequest = Body(default_factory=QuickFixRequest),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> QuickFixResponse:
    """Auto-fix missing story fields by business_id."""
    story = get_story_by_identifier(db, None, story_business_id, current_user)
    service = StoryQuickFixService(db)
    return await service.fix_story(story, dry_run=request.dry_run)
