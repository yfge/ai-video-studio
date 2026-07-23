"""Lightweight story seed contract used before novel adaptation."""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StorySeedProtagonist(BaseModel):
    virtual_ip_business_id: str = Field(..., min_length=1, max_length=32)
    initial_state: str = Field(..., min_length=1)


class StorySeedModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schema_version: str = Field(
        "story_seed_v1", alias="schema", pattern="^story_seed_v1$"
    )
    title: str = Field(..., min_length=1, max_length=255)
    premise: str = Field(..., min_length=1)
    outline: str = Field(..., min_length=1)
    protagonists: List[StorySeedProtagonist] = Field(..., min_length=1)
    world_constraints: List[str] = Field(default_factory=list)
    central_conflict: str = Field(..., min_length=1)
    ending_direction: Optional[str] = None
    target_audience: Optional[str] = Field(None, max_length=100)
    content_constraints: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_business_ids_are_unique(self):
        identifiers = [item.virtual_ip_business_id for item in self.protagonists]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("protagonist virtual_ip_business_id must be unique")
        return self


class StorySeedEnvelope(BaseModel):
    story_seed: StorySeedModel


def extract_story_seed_envelope(data) -> dict:
    """Keep the envelope intact for structured-output validation."""
    if isinstance(data, dict) and isinstance(data.get("story_seed"), dict):
        return {"story_seed": data["story_seed"]}
    return {}
