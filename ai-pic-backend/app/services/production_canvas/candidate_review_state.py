from datetime import datetime
from typing import Literal

from app.repositories.production_canvas_candidate_repository import (
    ProductionCanvasCandidateRepository,
)
from sqlalchemy.orm import Session

from .candidate_history import CanvasCandidateReference, _metadata, _references


def set_canvas_candidate_review(
    db: Session,
    *,
    run_id: str,
    node_id: str,
    candidate_id: int,
    review_state: Literal["approved", "rejected"],
    reviewed_by: int,
    reviewed_at: datetime,
    rejection_reason: str | None = None,
) -> None:
    repository = ProductionCanvasCandidateRepository(db)
    asset = repository.get_by_id(candidate_id)
    if asset is None:
        raise ValueError("canvas_candidate_not_found")
    references = _references(asset)
    matched = False
    updated: list[CanvasCandidateReference] = []
    for reference in references:
        if reference.run_id == run_id and reference.node_id == node_id:
            matched = True
            reference = reference.model_copy(
                update={
                    "review_state": review_state,
                    "reviewed_by": reviewed_by,
                    "reviewed_at": reviewed_at,
                    "rejection_reason": (
                        rejection_reason.strip() or None
                        if isinstance(rejection_reason, str)
                        else None
                    ),
                }
            )
        updated.append(reference)
    if not matched:
        raise ValueError("canvas_candidate_not_found")
    metadata = _metadata(asset)
    metadata["canvas_candidate_refs"] = [
        item.model_dump(mode="json") for item in updated
    ]
    asset.extra_metadata = metadata
    db.add(asset)
