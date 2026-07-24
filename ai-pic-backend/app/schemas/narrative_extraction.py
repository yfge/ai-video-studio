"""Provider output schema for narrative-memory candidate extraction."""

import re
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


def _require_semantic_evidence(value: str) -> str:
    value = value.strip()
    if len(re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "", value)) < 3:
        raise ValueError("evidence must contain at least 3 semantic characters")
    return value


class NarrativeExtractionRequest(BaseModel):
    source_scope: Literal["story_seed", "canonical_novel", "novel_chapter"] = (
        "canonical_novel"
    )
    source_artifact_business_id: Optional[str] = None
    model: Optional[str] = None

    @model_validator(mode="after")
    def require_chapter_id(self):
        if (
            self.source_scope == "novel_chapter"
            and not self.source_artifact_business_id
        ):
            raise ValueError(
                "novel_chapter extraction requires source_artifact_business_id"
            )
        return self


class ExtractedEvent(BaseModel):
    event_type: Literal[
        "action", "reveal", "relationship", "state_change", "world_fact"
    ]
    summary: str
    typed_event_ids: list[str] = Field(default_factory=list)
    participant_character_ids: list[str] = Field(default_factory=list)
    occurred_at_anchor_business_id: str
    presentation: Literal["on_screen", "offscreen", "withheld"] = "on_screen"
    audience_disclosure: Literal["hidden", "hinted", "partial", "revealed"] = "revealed"
    evidence: str = Field(..., min_length=3)

    _validate_evidence = field_validator("evidence")(_require_semantic_evidence)


class ExtractedMemory(BaseModel):
    character_business_id: str
    virtual_ip_business_id: str
    typed_character_id: Optional[str] = None
    typed_fact_id: Optional[str] = None
    typed_source_event_id: Optional[str] = None
    memory_type: Literal[
        "witnessed", "heard", "inferred", "dreamed", "misled", "remembered"
    ]
    content: str
    belief: Optional[str] = None
    belief_confidence: Optional[float] = Field(None, ge=0, le=1)
    perception: Optional[str] = None
    emotional_impact: list[str] = Field(default_factory=list)
    salience: float = Field(0.5, ge=0, le=1)
    occurred_at_anchor_business_id: str
    learned_at_anchor_business_id: str
    effective_from_anchor_business_id: str
    invalidated_at_anchor_business_id: Optional[str] = None
    growth_delta: Optional[dict] = None
    evidence: str = Field(..., min_length=3)

    _validate_evidence = field_validator("evidence")(_require_semantic_evidence)


class NarrativeExtractionEnvelope(BaseModel):
    events: list[ExtractedEvent] = Field(default_factory=list)
    memories: list[ExtractedMemory] = Field(default_factory=list)
