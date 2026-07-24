"""Versioned story seed contracts used before novel adaptation."""

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StorySeedProtagonist(BaseModel):
    virtual_ip_business_id: str = Field(..., min_length=1, max_length=32)
    initial_state: str = Field(..., min_length=1)


class StorySeedStructuredChapter(BaseModel):
    position: int = Field(..., strict=True, ge=1)
    title: str = Field(..., min_length=1, max_length=255)
    goal: str = Field(..., min_length=1)
    key_events: List[str] = Field(..., min_length=1)
    character_focus: List[str] = Field(default_factory=list)
    open_threads: List[str] = Field(default_factory=list)
    end_state: str = Field(..., min_length=1)


class StorySeedThreadPayoff(BaseModel):
    thread_id: str = Field(..., min_length=1)
    payoff_position: int = Field(..., strict=True, ge=1)
    evidence_key_event: str = Field(..., min_length=1)


class StorySeedStructuredOutline(BaseModel):
    status: Literal["draft", "confirmed", "frozen"] = "draft"
    version: int = Field(..., strict=True, ge=1)
    chapters: List[StorySeedStructuredChapter] = Field(..., min_length=1)
    thread_schedule_version: int = Field(0, strict=True, ge=0, le=1)
    thread_payoffs: List[StorySeedThreadPayoff] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_contiguous_positions(self):
        positions = [item.position for item in self.chapters]
        if positions != list(range(1, len(self.chapters) + 1)):
            raise ValueError("chapter positions must start at 1 and be contiguous")
        return self


class StorySeedModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schema_version: Literal["story_seed_v1", "story_seed_v2"] = Field(
        "story_seed_v1", alias="schema"
    )
    title: str = Field(..., min_length=1, max_length=255)
    premise: str = Field(..., min_length=1)
    outline: Optional[str] = Field(None, min_length=1)
    outline_text: Optional[str] = Field(None, min_length=1)
    structured_outline: Optional[StorySeedStructuredOutline] = None
    protagonists: List[StorySeedProtagonist] = Field(..., min_length=1)
    world_constraints: List[str] = Field(default_factory=list)
    central_conflict: str = Field(..., min_length=1)
    ending_direction: Optional[str] = None
    target_audience: Optional[str] = Field(None, max_length=100)
    content_constraints: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_version_and_business_ids(self):
        identifiers = [item.virtual_ip_business_id for item in self.protagonists]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("protagonist virtual_ip_business_id must be unique")
        if self.schema_version == "story_seed_v1" and not self.outline:
            raise ValueError("story_seed_v1 requires outline")
        if self.schema_version == "story_seed_v2" and (
            not self.outline_text or not self.structured_outline
        ):
            raise ValueError(
                "story_seed_v2 requires outline_text and structured_outline"
            )
        return self


class StorySeedEnvelope(BaseModel):
    story_seed: StorySeedModel


class StorySeedStructuredUpdateRequest(BaseModel):
    outline_text: str = Field(..., min_length=1)
    structured_outline: StorySeedStructuredOutline
    story_seed_status: Literal["draft", "confirmed"]
    story_seed_version: int = Field(..., strict=True, ge=1)


def extract_story_seed_envelope(data) -> dict:
    """Keep the envelope intact for structured-output validation."""
    if isinstance(data, dict) and isinstance(data.get("story_seed"), dict):
        return {"story_seed": data["story_seed"]}
    return {}
