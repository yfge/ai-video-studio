"""Contracts for narrative anchors, events, memories, snapshots, and review."""

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator

CandidateStatus = Literal["candidate", "approved", "rejected", "stale", "superseded"]
AnchorType = Literal["chapter", "episode", "scene", "beat", "between"]


class NarrativeAnchorCreate(BaseModel):
    anchor_type: AnchorType
    narrative_sequence: int = Field(..., ge=0)
    story_time_order: Optional[int] = None
    story_time_label: Optional[str] = Field(None, max_length=128)
    story_time_metadata: Optional[dict[str, Any]] = None
    chapter_business_id: Optional[str] = None
    episode_business_id: Optional[str] = None
    script_business_id: Optional[str] = None
    scene_business_id: Optional[str] = None
    beat_id: Optional[str] = None
    after_anchor_business_id: Optional[str] = None
    before_anchor_business_id: Optional[str] = None
    source_artifact_type: str = Field(..., max_length=32)
    source_artifact_business_id: str = Field(..., max_length=64)
    source_version: int = Field(1, ge=1)
    source_hash: str = Field(..., min_length=1, max_length=64)

    @model_validator(mode="after")
    def validate_between_anchor(self):
        if self.anchor_type == "between" and not (
            self.after_anchor_business_id and self.before_anchor_business_id
        ):
            raise ValueError("between anchor requires after and before anchors")
        return self


class NarrativeAnchorResponse(NarrativeAnchorCreate):
    business_id: str
    story_business_id: str
    canon_branch_id: str
    status: str
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NarrativeEventCandidateCreate(BaseModel):
    candidate_kind: Literal["event"] = "event"
    event_type: Literal[
        "action", "reveal", "relationship", "state_change", "world_fact"
    ]
    summary: str = Field(..., min_length=1)
    participant_character_ids: list[str] = Field(default_factory=list)
    occurred_at_anchor_business_id: str
    presentation: Literal["on_screen", "offscreen", "withheld"] = "on_screen"
    audience_disclosure: Literal["hidden", "hinted", "partial", "revealed"] = "revealed"
    source_artifact_type: str
    source_artifact_business_id: str
    source_version: int = Field(1, ge=1)
    source_hash: str
    candidate_evidence: Optional[dict[str, Any]] = None


class CharacterMemoryCandidateCreate(BaseModel):
    candidate_kind: Literal["memory"] = "memory"
    character_business_id: str
    virtual_ip_business_id: str
    memory_type: Literal[
        "witnessed", "heard", "inferred", "dreamed", "misled", "remembered"
    ]
    event_business_id: Optional[str] = None
    content: str = Field(..., min_length=1)
    belief: Optional[str] = None
    belief_confidence: Optional[float] = Field(None, ge=0, le=1)
    perception: Optional[str] = None
    emotional_impact: list[str] = Field(default_factory=list)
    salience: float = Field(0.5, ge=0, le=1)
    occurred_at_anchor_business_id: str
    learned_at_anchor_business_id: str
    effective_from_anchor_business_id: str
    invalidated_at_anchor_business_id: Optional[str] = None
    source_artifact_type: str
    source_artifact_business_id: str
    source_version: int = Field(1, ge=1)
    source_hash: str
    candidate_evidence: Optional[dict[str, Any]] = None


class CandidateDeltaCreate(BaseModel):
    anchors: list[NarrativeAnchorCreate] = Field(default_factory=list)
    events: list[NarrativeEventCandidateCreate] = Field(default_factory=list)
    memories: list[CharacterMemoryCandidateCreate] = Field(default_factory=list)


class CandidateUpdate(BaseModel):
    expected_version: int = Field(..., ge=1)
    summary: Optional[str] = None
    content: Optional[str] = None
    belief: Optional[str] = None
    belief_confidence: Optional[float] = Field(None, ge=0, le=1)
    salience: Optional[float] = Field(None, ge=0, le=1)
    occurred_at_anchor_business_id: Optional[str] = None
    learned_at_anchor_business_id: Optional[str] = None
    effective_from_anchor_business_id: Optional[str] = None
    invalidated_at_anchor_business_id: Optional[str] = None
    presentation: Optional[Literal["on_screen", "offscreen", "withheld"]] = None
    audience_disclosure: Optional[
        Literal["hidden", "hinted", "partial", "revealed"]
    ] = None


class CandidateReviewRequest(BaseModel):
    expected_version: int = Field(..., ge=1)
    reason: Optional[str] = None


class CandidateSplitRequest(BaseModel):
    expected_version: int = Field(..., ge=1)
    contents: list[str] = Field(..., min_length=2, max_length=12)


class CandidateMergeRequest(BaseModel):
    candidate_business_ids: list[str] = Field(..., min_length=2, max_length=12)
    expected_versions: dict[str, int]
    merged_content: Optional[str] = None


class NarrativeEventResponse(BaseModel):
    business_id: str
    story_business_id: str
    canon_branch_id: str
    event_type: str
    summary: str
    participant_character_ids: list[str] = Field(default_factory=list)
    occurred_at_anchor_business_id: str
    presentation: str
    audience_disclosure: str
    status: CandidateStatus
    source_artifact_type: str
    source_artifact_business_id: str
    source_version: int
    source_hash: str
    candidate_evidence: Optional[dict[str, Any]] = None
    invalidation: Optional[dict[str, Any]] = None
    supersedes_business_id: Optional[str] = None
    version: int
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CharacterMemoryResponse(BaseModel):
    business_id: str
    story_business_id: Optional[str] = None
    canon_branch_id: str
    character_business_id: Optional[str] = None
    virtual_ip_business_id: str
    scope: Literal["story_private", "character_shared"]
    memory_type: str
    event_business_id: Optional[str] = None
    content: str
    belief: Optional[str] = None
    belief_confidence: Optional[float] = None
    perception: Optional[str] = None
    emotional_impact: list[str] = Field(default_factory=list)
    salience: float
    occurred_at_anchor_business_id: Optional[str] = None
    learned_at_anchor_business_id: str
    effective_from_anchor_business_id: str
    invalidated_at_anchor_business_id: Optional[str] = None
    status: CandidateStatus
    source_hash: str
    candidate_evidence: Optional[dict[str, Any]] = None
    invalidation: Optional[dict[str, Any]] = None
    supersedes_business_id: Optional[str] = None
    version: int
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SnapshotRebuildRequest(BaseModel):
    character_business_id: str
    as_of_anchor_business_id: str


class MemorySnapshotResponse(BaseModel):
    business_id: str
    story_business_id: str
    canon_branch_id: str
    character_business_id: str
    virtual_ip_business_id: str
    as_of_anchor_business_id: str
    shared_baseline_version: int
    approved_memory_watermark: int
    included_memory_ids: list[str]
    growth_state: dict[str, Any]
    snapshot_hash: str
    is_stale: bool
    stale_reason: Optional[dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MemorySummaryResponse(BaseModel):
    canon_branch_id: str
    private_memory_count: int
    shared_baseline_version: int
    shared_baseline_hash: Optional[str] = None
    latest_snapshot_hash: Optional[str] = None
    pending_count: int
    conflict_count: int
    stale_count: int
    memory_review_status: str


class BaselineSyncRequest(BaseModel):
    expected_version: int = Field(..., ge=0)
    confirm: bool
