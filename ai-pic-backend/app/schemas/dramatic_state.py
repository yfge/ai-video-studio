"""Scene intent, audience disclosure, and subtext contracts."""

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class CharacterIntent(BaseModel):
    character_business_id: str
    surface_action: str
    hidden_goal: Optional[str] = None
    emotional_truth: Optional[str] = None
    expression_policy: Literal["sayable", "subtext_only", "must_not_reveal"] = "sayable"


class DramaticStatePayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schema_version: Literal["dramatic_state.v1"] = Field(
        "dramatic_state.v1", alias="schema"
    )
    valid_from_anchor_id: Optional[str] = None
    valid_until_anchor_id: Optional[str] = None
    scene_objective: Optional[str] = None
    character_intents: list[CharacterIntent] = Field(default_factory=list)
    audience_goal: Optional[str] = None
    audience_disclosure: Literal["hidden", "hinted", "partial", "revealed"] = "revealed"
    must_hint: list[str] = Field(default_factory=list)
    must_not_reveal: list[str] = Field(default_factory=list)


class DramaticStateUpdate(BaseModel):
    expected_version: int = Field(..., ge=0)
    dramatic_state: DramaticStatePayload


class DramaticStateSuggestRequest(BaseModel):
    expected_version: int = Field(..., ge=0)
    model: Optional[str] = None


class DramaticStateResponse(BaseModel):
    scene_business_id: str
    version: int
    state_hash: str
    dramatic_state: DramaticStatePayload
    quality_gate: dict
    suggestion: Optional[DramaticStatePayload] = None
    suggestion_based_on_version: Optional[int] = None
    available_memory_preview: list[dict] = Field(default_factory=list)
