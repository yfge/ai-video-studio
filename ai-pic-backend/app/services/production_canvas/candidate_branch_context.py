from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.models.user import User
from app.schemas.production_canvas import ProductionCanvasSkillExecuteRequest
from app.schemas.production_canvas_review import ProductionCanvasMediaCandidate
from sqlalchemy.orm import Session

from .candidate_review import list_canvas_media_candidates


@dataclass(frozen=True)
class CanvasCandidateBranchContext:
    candidate: ProductionCanvasMediaCandidate
    instruction: str | None
    metadata: dict[str, Any]

    @property
    def prompt(self) -> str | None:
        if self.instruction and self.candidate.prompt:
            return (
                f"{self.candidate.prompt}\n\n"
                f"Branch variation instruction: {self.instruction}"
            )
        return self.instruction or self.candidate.prompt


def resolve_canvas_candidate_branch(
    db: Session,
    user: User,
    request: ProductionCanvasSkillExecuteRequest,
    *,
    media_type: str,
) -> CanvasCandidateBranchContext | None:
    candidate_id = request.branch_parent_candidate_id
    if candidate_id is None:
        return None
    if not request.run_id or not request.node_id:
        raise ValueError("canvas_branch_context_missing")
    review = list_canvas_media_candidates(db, user, request.run_id, request.node_id)
    candidate = next(
        (item for item in review.candidates if item.asset_id == candidate_id), None
    )
    if candidate is None:
        raise ValueError("canvas_candidate_not_found")
    if candidate.media_type != media_type:
        raise ValueError("canvas_candidate_media_type_mismatch")
    instruction = (
        request.branch_instruction.strip()
        if isinstance(request.branch_instruction, str)
        and request.branch_instruction.strip()
        else None
    )
    return CanvasCandidateBranchContext(
        candidate=candidate,
        instruction=instruction,
        metadata={
            "run_id": request.run_id,
            "node_id": request.node_id,
            "parent_candidate_id": candidate.asset_id,
            "instruction": instruction,
        },
    )
