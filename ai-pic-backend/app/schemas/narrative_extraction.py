"""Provider output schema for narrative-memory candidate extraction."""

from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


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
    participant_character_ids: list[str] = Field(default_factory=list)
    occurred_at_anchor_business_id: str
    presentation: Literal["on_screen", "offscreen", "withheld"] = "on_screen"
    audience_disclosure: Literal["hidden", "hinted", "partial", "revealed"] = "revealed"


class ExtractedMemory(BaseModel):
    character_business_id: str
    virtual_ip_business_id: str
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


class NarrativeExtractionEnvelope(BaseModel):
    events: list[ExtractedEvent] = Field(default_factory=list)
    memories: list[ExtractedMemory] = Field(default_factory=list)
