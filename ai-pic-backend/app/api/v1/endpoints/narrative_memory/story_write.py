"""Story memory mutation and manual review endpoints."""

import json

from app.api.v1.endpoints.narrative_memory.dependencies import owned_story
from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.task import Task, TaskType
from app.models.user import User
from app.repositories.narrative_promotion_repository import NarrativePromotionRepository
from app.schemas.narrative_extraction import NarrativeExtractionRequest
from app.schemas.narrative_memory import (
    BaselineSyncRequest,
    CandidateDeltaCreate,
    CandidateMergeRequest,
    CandidateReviewRequest,
    CandidateSplitRequest,
    CandidateUpdate,
    CharacterMemoryResponse,
    MemorySnapshotResponse,
    NarrativeAnchorCreate,
    NarrativeAnchorResponse,
    NarrativeEventResponse,
    SnapshotRebuildRequest,
)
from app.services.narrative_memory.anchor_service import AnchorService
from app.services.narrative_memory.baseline_service import BaselineService
from app.services.narrative_memory.candidate_composition_service import (
    CandidateCompositionService,
)
from app.services.narrative_memory.candidate_service import CandidateService
from app.services.narrative_memory.snapshot_service import SnapshotService
from app.services.task_worker import narrative_memory_extract_task
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()


def _candidate_response(kind: str, entity):
    model = NarrativeEventResponse if kind == "event" else CharacterMemoryResponse
    return model.model_validate(entity)


@router.post(
    "/business/{story_business_id}/narrative-memory/extract-async",
    status_code=202,
)
def extract_candidates_async(
    story_business_id: str,
    payload: NarrativeExtractionRequest,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    owned_story(db, story_business_id, user)
    values = payload.model_dump()
    task = Task(
        title="提取叙事记忆候选",
        description="显式模型任务：只创建待人工审核候选",
        task_type=TaskType.TEXT_GENERATION,
        target_business_id=story_business_id,
        parameters=json.dumps(
            {"operation": "narrative_memory_extract", **values}, ensure_ascii=False
        ),
        user_id=user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    narrative_memory_extract_task.delay(task.id, story_business_id, values, user.id)
    return {"success": True, "data": {"task_id": task.id, "status": task.status}}


@router.post(
    "/business/{story_business_id}/narrative-memory/anchors",
    response_model=NarrativeAnchorResponse,
    status_code=201,
)
def create_anchor(
    story_business_id: str,
    payload: NarrativeAnchorCreate,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    repo, story = owned_story(db, story_business_id, user)
    return AnchorService(repo).create(story, payload, user.id)


@router.post(
    "/business/{story_business_id}/narrative-memory/candidates", status_code=201
)
def ingest_candidates(
    story_business_id: str,
    payload: CandidateDeltaCreate,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    repo, story = owned_story(db, story_business_id, user)
    result = CandidateService(repo).ingest(story, payload, user)
    return {
        "anchors": [
            NarrativeAnchorResponse.model_validate(v) for v in result["anchors"]
        ],
        "events": [NarrativeEventResponse.model_validate(v) for v in result["events"]],
        "memories": [
            CharacterMemoryResponse.model_validate(v) for v in result["memories"]
        ],
    }


@router.patch(
    "/business/{story_business_id}/narrative-memory/candidates/{candidate_business_id}"
)
def update_candidate(
    story_business_id: str,
    candidate_business_id: str,
    payload: CandidateUpdate,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    repo, story = owned_story(db, story_business_id, user)
    kind, entity = CandidateService(repo).update(story, candidate_business_id, payload)
    return _candidate_response(kind, entity)


def _review_candidate(story_id, candidate_id, payload, user, db, approved):
    repo, story = owned_story(db, story_id, user)
    kind, entity = CandidateService(repo).review(
        story,
        candidate_id,
        expected_version=payload.expected_version,
        approved=approved,
        user_id=user.id,
        reason=payload.reason,
    )
    return _candidate_response(kind, entity)


@router.post(
    "/business/{story_business_id}/narrative-memory/candidates/{candidate_business_id}/approve"
)
def approve_candidate(
    story_business_id: str,
    candidate_business_id: str,
    payload: CandidateReviewRequest,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return _review_candidate(
        story_business_id, candidate_business_id, payload, user, db, True
    )


@router.post(
    "/business/{story_business_id}/narrative-memory/candidates/{candidate_business_id}/reject"
)
def reject_candidate(
    story_business_id: str,
    candidate_business_id: str,
    payload: CandidateReviewRequest,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return _review_candidate(
        story_business_id, candidate_business_id, payload, user, db, False
    )


@router.post(
    "/business/{story_business_id}/narrative-memory/candidates/{candidate_business_id}/split"
)
def split_candidate(
    story_business_id: str,
    candidate_business_id: str,
    payload: CandidateSplitRequest,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    repo, story = owned_story(db, story_business_id, user)
    kind, entities = CandidateCompositionService(repo).split(
        story,
        candidate_business_id,
        expected_version=payload.expected_version,
        contents=payload.contents,
        user_id=user.id,
    )
    return [_candidate_response(kind, entity) for entity in entities]


@router.post("/business/{story_business_id}/narrative-memory/candidates/merge")
def merge_candidates(
    story_business_id: str,
    payload: CandidateMergeRequest,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    repo, story = owned_story(db, story_business_id, user)
    kind, entity = CandidateCompositionService(repo).merge(
        story,
        business_ids=payload.candidate_business_ids,
        expected_versions=payload.expected_versions,
        merged_content=payload.merged_content,
        user_id=user.id,
    )
    return _candidate_response(kind, entity)


@router.post(
    "/business/{story_business_id}/narrative-memory/snapshots/rebuild",
    response_model=MemorySnapshotResponse,
)
def rebuild_snapshot(
    story_business_id: str,
    payload: SnapshotRebuildRequest,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    repo, story = owned_story(db, story_business_id, user)
    return SnapshotService(repo).rebuild(
        story,
        character_business_id=payload.character_business_id,
        as_of_anchor_business_id=payload.as_of_anchor_business_id,
    )


@router.post("/business/{story_business_id}/narrative-memory/shared-baseline/sync")
def sync_baseline(
    story_business_id: str,
    payload: BaselineSyncRequest,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    repo, story = owned_story(db, story_business_id, user)
    service = BaselineService(repo, NarrativePromotionRepository(db))
    return service.sync(
        story, expected_version=payload.expected_version, confirm=payload.confirm
    )
