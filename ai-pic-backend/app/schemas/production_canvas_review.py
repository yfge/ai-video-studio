from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ProductionCanvasMediaCandidate(BaseModel):
    asset_id: int
    asset_business_id: str
    media_type: Literal["image", "video"]
    url: str
    frame_index: int
    clip_id: str | None = None
    prompt: str | None = None
    model: str | None = None
    duration_seconds: float | None = None
    selected: bool = False
    review_state: Literal["pending", "approved", "rejected"] = "pending"
    reviewed_by: int | None = None
    reviewed_at: datetime | None = None
    rejection_reason: str | None = None


class ProductionCanvasStaleImpactNode(BaseModel):
    node_id: str
    title: str


class ProductionCanvasMediaCandidateList(BaseModel):
    node_id: str
    selected_output_id: int | None = None
    stale_impact: list[ProductionCanvasStaleImpactNode] = Field(default_factory=list)
    candidates: list[ProductionCanvasMediaCandidate] = Field(default_factory=list)


class ProductionCanvasCandidateApprovalRequest(BaseModel):
    candidate_id: int = Field(..., ge=1)


class ProductionCanvasCandidateRejectionRequest(BaseModel):
    candidate_id: int = Field(..., ge=1)
    reason: str | None = Field(None, max_length=500)


class ProductionCanvasTimelinePlacementRequest(BaseModel):
    expected_version: int = Field(..., ge=1)
