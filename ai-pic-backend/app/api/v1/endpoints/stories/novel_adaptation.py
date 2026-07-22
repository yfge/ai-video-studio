from __future__ import annotations

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.user import User
from app.schemas.script import EpisodeResponse
from app.schemas.story_novel_export import (
    StoryNovelAdaptationPlanApproveRequest,
    StoryNovelAdaptationPlanUpdateRequest,
    StoryNovelRevisionResponse,
)
from app.services.story.story_novel_adaptation_service import (
    StoryNovelAdaptationService,
)
from app.services.story.story_novel_revision_service import StoryNovelRevisionService
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .novel_task_queue import queue_novel_operation

router = APIRouter()


@router.post("/novel/revisions/{revision_business_id}/adaptation-plan/generate-async")
def generate_adaptation_plan(
    revision_business_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    revision = StoryNovelRevisionService(db, current_user).revision(
        revision_business_id
    )
    return queue_novel_operation(db, current_user, revision, "generate_adaptation_plan")


@router.patch(
    "/novel/revisions/{revision_business_id}/adaptation-plan",
    response_model=StoryNovelRevisionResponse,
)
def save_adaptation_plan(
    revision_business_id: str,
    request: StoryNovelAdaptationPlanUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return StoryNovelAdaptationService(db, current_user).save_plan(
        revision_business_id, request
    )


@router.post(
    "/novel/revisions/{revision_business_id}/adaptation-plan/approve",
    response_model=StoryNovelRevisionResponse,
)
def approve_adaptation_plan(
    revision_business_id: str,
    request: StoryNovelAdaptationPlanApproveRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return StoryNovelAdaptationService(db, current_user).approve_plan(
        revision_business_id, request.expected_version
    )


@router.post(
    "/novel/revisions/{revision_business_id}/adaptation-plan/apply",
    response_model=list[EpisodeResponse],
)
def apply_adaptation_plan(
    revision_business_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return StoryNovelAdaptationService(db, current_user).apply_plan(
        revision_business_id
    )
