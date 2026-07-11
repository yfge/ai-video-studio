from __future__ import annotations

from datetime import datetime
from typing import Literal

from app.models.timeline import MediaAsset
from app.models.user import User
from app.repositories.production_canvas_candidate_repository import (
    ProductionCanvasCandidateRepository,
)
from app.schemas.production_canvas import ProductionCanvasSavedNode
from app.schemas.production_canvas_review import ProductionCanvasMediaCandidate
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.orm import Session


class CanvasCandidateReference(BaseModel):
    run_id: str = Field(..., min_length=1, max_length=32)
    node_id: str = Field(..., min_length=1, max_length=120)
    frame_index: int = Field(..., ge=0)
    clip_id: str | None = None
    prompt: str | None = None
    model: str | None = None
    duration_seconds: float | None = None
    review_state: Literal["pending", "approved", "rejected"] = "pending"
    reviewed_by: int | None = None
    reviewed_at: datetime | None = None
    rejection_reason: str | None = None
    parent_candidate_id: int | None = Field(None, ge=1)
    branch_task_id: int | None = Field(None, ge=1)
    branch_instruction: str | None = None


def _metadata(asset: MediaAsset) -> dict:
    return dict(asset.extra_metadata) if isinstance(asset.extra_metadata, dict) else {}


def _references(asset: MediaAsset) -> list[CanvasCandidateReference]:
    raw = _metadata(asset).get("canvas_candidate_refs")
    references: list[CanvasCandidateReference] = []
    for item in raw if isinstance(raw, list) else []:
        try:
            references.append(CanvasCandidateReference.model_validate(item))
        except ValidationError:
            continue
    return references


def _candidate_from_asset(
    asset: MediaAsset,
    reference: CanvasCandidateReference,
    selected_output_id: int | None,
) -> ProductionCanvasMediaCandidate | None:
    if asset.is_deleted or not asset.file_url:
        return None
    metadata = _metadata(asset)
    selected = asset.id == selected_output_id
    return ProductionCanvasMediaCandidate(
        asset_id=asset.id,
        asset_business_id=asset.business_id,
        media_type=asset.asset_type,
        url=asset.file_url,
        frame_index=reference.frame_index,
        clip_id=reference.clip_id or metadata.get("clip_id"),
        prompt=reference.prompt or metadata.get("prompt"),
        model=reference.model or metadata.get("model"),
        duration_seconds=(
            reference.duration_seconds
            if reference.duration_seconds is not None
            else asset.duration_ms / 1000 if asset.duration_ms else None
        ),
        selected=selected,
        review_state="approved" if selected else reference.review_state,
        reviewed_by=reference.reviewed_by,
        reviewed_at=reference.reviewed_at,
        rejection_reason=None if selected else reference.rejection_reason,
        parent_candidate_id=reference.parent_candidate_id,
        branch_task_id=reference.branch_task_id,
        branch_instruction=reference.branch_instruction,
    )


def _selected_reference(
    asset: MediaAsset,
    run_id: str,
    node: ProductionCanvasSavedNode,
) -> CanvasCandidateReference:
    metadata = _metadata(asset)
    return CanvasCandidateReference(
        run_id=run_id,
        node_id=node.id,
        frame_index=max(int(metadata.get("frame_index") or 0), 0),
        clip_id=node.outputs.get("selected_output_clip_id") or metadata.get("clip_id"),
        prompt=metadata.get("prompt"),
        model=metadata.get("model"),
        duration_seconds=asset.duration_ms / 1000 if asset.duration_ms else None,
    )


def load_canvas_candidate_history(
    db: Session,
    user: User,
    run_id: str,
    node: ProductionCanvasSavedNode,
    media_type: str,
) -> list[ProductionCanvasMediaCandidate]:
    repository = ProductionCanvasCandidateRepository(db)
    candidates: list[ProductionCanvasMediaCandidate] = []
    for asset in repository.list_history_assets(
        created_by=user.id, asset_type=media_type
    ):
        for reference in _references(asset):
            if reference.run_id != run_id or reference.node_id != node.id:
                continue
            candidate = _candidate_from_asset(asset, reference, node.selected_output_id)
            if candidate is not None:
                candidates.append(candidate)
    if node.selected_output_id and not any(
        item.asset_id == node.selected_output_id for item in candidates
    ):
        asset = repository.get_by_id(node.selected_output_id)
        if (
            asset is not None
            and asset.asset_type == media_type
            and asset.created_by in {None, user.id}
        ):
            candidate = _candidate_from_asset(
                asset,
                _selected_reference(asset, run_id, node),
                node.selected_output_id,
            )
            if candidate is not None:
                candidates.append(candidate)
    return candidates


def materialize_canvas_candidate(
    db: Session,
    user: User,
    *,
    media_type: str,
    url: str,
    frame_index: int,
    clip_id: str | None,
    prompt: str | None,
    model: str | None,
    duration_seconds: float | None,
    selected_output_id: int | None,
    parent_candidate_id: int | None = None,
    branch_task_id: int | None = None,
    branch_instruction: str | None = None,
) -> ProductionCanvasMediaCandidate:
    repository = ProductionCanvasCandidateRepository(db)
    asset = repository.find_owned_by_location(
        created_by=user.id, asset_type=media_type, file_url=url
    )
    if asset is None:
        asset = repository.create(
            asset_type=media_type,
            origin="provider",
            file_url=url,
            duration_ms=(
                int(duration_seconds * 1000) if duration_seconds is not None else None
            ),
            extra_metadata={
                "kind": "production_canvas_candidate",
                "frame_index": frame_index,
                "clip_id": clip_id,
                "prompt": prompt,
                "model": model,
            },
            created_by=user.id,
        )
        db.flush()
    return ProductionCanvasMediaCandidate(
        asset_id=asset.id,
        asset_business_id=asset.business_id,
        media_type=media_type,
        url=url,
        frame_index=frame_index,
        clip_id=clip_id,
        prompt=prompt,
        model=model,
        duration_seconds=duration_seconds,
        selected=asset.id == selected_output_id,
        parent_candidate_id=parent_candidate_id,
        branch_task_id=branch_task_id,
        branch_instruction=branch_instruction,
    )


def remember_canvas_candidate_history(
    db: Session,
    run_id: str,
    node: ProductionCanvasSavedNode,
    candidates: list[ProductionCanvasMediaCandidate],
) -> None:
    repository = ProductionCanvasCandidateRepository(db)
    for candidate in candidates:
        asset = repository.get_by_id(candidate.asset_id)
        if asset is None:
            continue
        reference = CanvasCandidateReference(
            run_id=run_id,
            node_id=node.id,
            frame_index=candidate.frame_index,
            clip_id=candidate.clip_id,
            prompt=candidate.prompt,
            model=candidate.model,
            duration_seconds=candidate.duration_seconds,
            parent_candidate_id=candidate.parent_candidate_id,
            branch_task_id=candidate.branch_task_id,
            branch_instruction=candidate.branch_instruction,
        )
        references = _references(asset)
        identity = (reference.run_id, reference.node_id, reference.frame_index)
        if any(
            (item.run_id, item.node_id, item.frame_index) == identity
            for item in references
        ):
            continue
        metadata = _metadata(asset)
        metadata["canvas_candidate_refs"] = [
            *(item.model_dump(mode="json") for item in references),
            reference.model_dump(mode="json"),
        ]
        asset.extra_metadata = metadata
        db.add(asset)
