"""Virtual IP shared-memory and manual promotion endpoints."""

from app.api.v1.endpoints.narrative_memory.dependencies import promotion_repos
from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.core.middleware import get_current_active_user
from app.models.user import User
from app.schemas.narrative_memory import CharacterMemoryResponse
from app.schemas.narrative_promotion import (
    CharacterMemoryPromotionResponse,
    PromotionCandidateCreate,
    PromotionReviewRequest,
    PromotionUpdate,
    SharedMemoryCloneRequest,
    SharedMemorySupersedeRequest,
)
from app.services.narrative_memory.promotion_service import PromotionService
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

router = APIRouter()


def _service(db: Session) -> PromotionService:
    return PromotionService(*promotion_repos(db))


@router.get(
    "/virtual-ips/business/{virtual_ip_business_id}/memories",
    response_model=list[CharacterMemoryResponse],
)
def list_shared_memories(
    virtual_ip_business_id: str,
    canon_branch_id: str = Query("main", min_length=1, max_length=32),
    include_superseded: bool = Query(False),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _, repo = promotion_repos(db)
    target = repo.get_owned_virtual_ip(virtual_ip_business_id, user)
    if not target:
        raise NotFoundError.virtual_ip(virtual_ip_business_id)
    return repo.list_shared_memories(
        target.id,
        canon_branch_id=canon_branch_id,
        include_superseded=include_superseded,
    )


@router.get(
    "/virtual-ips/business/{virtual_ip_business_id}/memory-promotions",
    response_model=list[CharacterMemoryPromotionResponse],
)
def list_promotions(
    virtual_ip_business_id: str,
    canon_branch_id: str = Query("main", min_length=1, max_length=32),
    status: str | None = Query(None),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _, repo = promotion_repos(db)
    target = repo.get_owned_virtual_ip(virtual_ip_business_id, user)
    if not target:
        raise NotFoundError.virtual_ip(virtual_ip_business_id)
    return repo.list_promotions(
        target.id, canon_branch_id=canon_branch_id, status=status
    )


@router.post(
    "/character-memories/{memory_business_id}/promotion-candidates",
    response_model=CharacterMemoryPromotionResponse,
    status_code=201,
)
def create_promotion(
    memory_business_id: str,
    payload: PromotionCandidateCreate,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return _service(db).create_candidate(
        memory_business_id,
        payload.source_memory_ids,
        payload.candidate_content,
        user,
    )


@router.patch(
    "/character-memory-promotions/{promotion_business_id}",
    response_model=CharacterMemoryPromotionResponse,
)
def update_promotion(
    promotion_business_id: str,
    payload: PromotionUpdate,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return _service(db).update(
        promotion_business_id,
        expected_version=payload.expected_version,
        user=user,
        candidate_content=payload.candidate_content,
        decision_reason=payload.decision_reason,
    )


def _review(promotion_id, payload, user, db, approved):
    return _service(db).review(
        promotion_id,
        expected_version=payload.expected_version,
        approved=approved,
        reason=payload.reason,
        user=user,
    )


@router.post(
    "/character-memory-promotions/{promotion_business_id}/approve",
    response_model=CharacterMemoryPromotionResponse,
)
def approve_promotion(
    promotion_business_id: str,
    payload: PromotionReviewRequest,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return _review(promotion_business_id, payload, user, db, True)


@router.post(
    "/character-memory-promotions/{promotion_business_id}/reject",
    response_model=CharacterMemoryPromotionResponse,
)
def reject_promotion(
    promotion_business_id: str,
    payload: PromotionReviewRequest,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return _review(promotion_business_id, payload, user, db, False)


@router.post(
    "/virtual-ips/business/{virtual_ip_business_id}/memories/{memory_business_id}/clone",
    response_model=CharacterMemoryResponse,
)
def clone_shared_memory(
    virtual_ip_business_id: str,
    memory_business_id: str,
    payload: SharedMemoryCloneRequest,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return _service(db).clone_shared(
        virtual_ip_business_id,
        memory_business_id,
        content=payload.content,
        user=user,
    )


@router.post(
    "/virtual-ips/business/{virtual_ip_business_id}/memories/{memory_business_id}/supersede",
    response_model=CharacterMemoryResponse,
)
def supersede_shared_memory(
    virtual_ip_business_id: str,
    memory_business_id: str,
    payload: SharedMemorySupersedeRequest,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return _service(db).supersede_shared(
        virtual_ip_business_id,
        memory_business_id,
        expected_version=payload.expected_version,
        content=payload.content,
        user=user,
    )
