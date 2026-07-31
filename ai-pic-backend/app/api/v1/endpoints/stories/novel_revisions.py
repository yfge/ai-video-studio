from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.user import User
from app.repositories.story_novel_repository import StoryNovelRepository
from app.schemas.story_novel_export import (
    StoryNovelCanonUpdateRequest,
    StoryNovelCanonUpdateResponse,
    StoryNovelChapterReorderRequest,
    StoryNovelChapterResponse,
    StoryNovelChapterUpdateRequest,
    StoryNovelContinuityCheckRequest,
    StoryNovelContinuityIssueAcceptRequest,
    StoryNovelCreateRevisionRequest,
    StoryNovelGenerateRevisionRequest,
    StoryNovelLengthSpecUpdateRequest,
    StoryNovelRevisionListResponse,
    StoryNovelRevisionResponse,
)
from app.services.story.story_novel_revision_service import StoryNovelRevisionService

from .novel_task_queue import queue_novel_operation

router = APIRouter()


@router.post(
    "/business/{story_business_id}/novel/revisions",
    response_model=StoryNovelRevisionResponse,
)
def create_novel_revision(
    story_business_id: str,
    request: StoryNovelCreateRevisionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    revision = StoryNovelRevisionService(db, current_user).create_platform_draft(
        story_business_id, request
    )
    db.commit()
    db.refresh(revision)
    return revision


@router.get(
    "/business/{story_business_id}/novel/revisions",
    response_model=StoryNovelRevisionListResponse,
)
def list_novel_revisions(
    story_business_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = StoryNovelRevisionService(db, current_user)
    story = service.story(story_business_id)
    rows = service.repo.list_revisions(story.id, current_user)
    canonical = next(
        (row.business_id for row in rows if row.id == story.canonical_novel_export_id),
        None,
    )
    return {"items": rows, "canonical_business_id": canonical}


@router.get(
    "/novel/revisions/{revision_business_id}",
    response_model=StoryNovelRevisionResponse,
)
def get_novel_revision(
    revision_business_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return StoryNovelRevisionService(db, current_user).revision(revision_business_id)


@router.post("/novel/revisions/{revision_business_id}/generate-async")
def generate_novel_revision(
    revision_business_id: str,
    request: StoryNovelGenerateRevisionRequest | None = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = StoryNovelRevisionService(db, current_user)
    revision = service.revision(revision_business_id)
    service._ensure_draft(revision)
    response = queue_novel_operation(db, current_user, revision, "generate_revision")
    response["data"]["warnings"] = request.compatibility_warnings() if request else []
    return response


@router.patch(
    "/novel/revisions/{revision_business_id}/length-spec",
    response_model=StoryNovelRevisionResponse,
)
def update_novel_length_spec(
    revision_business_id: str,
    request: StoryNovelLengthSpecUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return StoryNovelRevisionService(db, current_user).update_length_spec(
        revision_business_id, request
    )


@router.post("/novel/revisions/{revision_business_id}/resume-async")
def resume_novel_revision(
    revision_business_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = StoryNovelRevisionService(db, current_user)
    revision = service.revision(revision_business_id)
    service._ensure_draft(revision)
    return queue_novel_operation(db, current_user, revision, "resume_revision")


@router.patch(
    "/novel/revisions/{revision_business_id}/chapters/{chapter_business_id}",
    response_model=StoryNovelChapterResponse,
)
def save_novel_chapter(
    revision_business_id: str,
    chapter_business_id: str,
    request: StoryNovelChapterUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return StoryNovelRevisionService(db, current_user).save_chapter(
        revision_business_id, chapter_business_id, request
    )


@router.post(
    "/novel/revisions/{revision_business_id}/chapters/reorder",
    response_model=StoryNovelRevisionResponse,
)
def reorder_novel_chapters(
    revision_business_id: str,
    request: StoryNovelChapterReorderRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return StoryNovelRevisionService(db, current_user).reorder(
        revision_business_id, request
    )


@router.post(
    "/novel/revisions/{revision_business_id}/chapters/{chapter_business_id}/regenerate-async"
)
def regenerate_novel_chapter(
    revision_business_id: str,
    chapter_business_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = StoryNovelRevisionService(db, current_user)
    revision = service.revision(revision_business_id)
    service._ensure_draft(revision)
    chapter = StoryNovelRepository(db).chapter(revision.id, chapter_business_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    return queue_novel_operation(
        db, current_user, revision, "regenerate_chapter", position=chapter.position
    )


@router.post(
    "/novel/revisions/{revision_business_id}/clone",
    response_model=StoryNovelRevisionResponse,
)
def clone_novel_revision(
    revision_business_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return StoryNovelRevisionService(db, current_user).clone(revision_business_id)


@router.post("/novel/revisions/{revision_business_id}/continuity-check-async")
def check_novel_continuity(
    revision_business_id: str,
    request: StoryNovelContinuityCheckRequest | None = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = StoryNovelRevisionService(db, current_user)
    revision = service.revision(revision_business_id)
    service._ensure_draft(revision)
    payload = {"review_model": request.review_model} if request else {}
    return queue_novel_operation(
        db, current_user, revision, "continuity_check", **payload
    )


@router.post(
    "/novel/revisions/{revision_business_id}/continuity-issues/{issue_id}/accept",
    response_model=StoryNovelRevisionResponse,
)
def accept_continuity_issue(
    revision_business_id: str,
    issue_id: str,
    request: StoryNovelContinuityIssueAcceptRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return StoryNovelRevisionService(db, current_user).accept_issue(
        revision_business_id, issue_id, request.reason
    )


@router.patch(
    "/novel/revisions/{revision_business_id}/canon",
    response_model=StoryNovelCanonUpdateResponse,
)
def update_novel_canon(
    revision_business_id: str,
    request: StoryNovelCanonUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    revision, canon_hash, stale_from = StoryNovelRevisionService(
        db, current_user
    ).update_canon(revision_business_id, request)
    return {
        "revision": revision,
        "canon_hash": canon_hash,
        "stale_from_position": stale_from,
    }


@router.post(
    "/novel/revisions/{revision_business_id}/approve",
    response_model=StoryNovelRevisionResponse,
)
def approve_novel_revision(
    revision_business_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return StoryNovelRevisionService(db, current_user).approve(revision_business_id)
