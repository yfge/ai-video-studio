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


class StorySeedGrowthCurves(BaseModel):
    cognition: Optional[str] = Field(None, min_length=1)
    capability: Optional[str] = Field(None, min_length=1)
    resources: Optional[str] = Field(None, min_length=1)
    activity_and_time_scale: Optional[str] = Field(None, min_length=1)


class StorySeedArcThread(BaseModel):
    thread_id: str = Field(..., min_length=1)
    question: str = Field(..., min_length=1)
    open_position: int = Field(..., strict=True, ge=1)
    payoff_position: int = Field(..., strict=True, ge=1)
    payoff_intent: str = Field(..., min_length=1)


class StorySeedProgressionArc(BaseModel):
    arc_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=255)
    start_position: int = Field(..., strict=True, ge=1)
    end_position: int = Field(..., strict=True, ge=1)
    narrative_goal: str = Field(..., min_length=1)
    ending_state: str = Field(..., min_length=1)
    growth: StorySeedGrowthCurves = Field(default_factory=StorySeedGrowthCurves)
    major_entries: List[str] = Field(default_factory=list)
    world_scope_changes: List[str] = Field(default_factory=list)
    threads: List[StorySeedArcThread] = Field(default_factory=list)


class StorySeedProgressionPlan(BaseModel):
    planning_structure_version: Literal[1] = 1
    requested_chapter_count: int = Field(..., strict=True, ge=1)
    progression_arcs: List[StorySeedProgressionArc] = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_arc_coverage(self):
        _validate_progression_arcs(self.progression_arcs, self.requested_chapter_count)
        return self


class StorySeedStructuredOutline(BaseModel):
    status: Literal["draft", "confirmed", "frozen"] = "draft"
    version: int = Field(..., strict=True, ge=1)
    requested_chapter_count: Optional[int] = Field(None, strict=True, ge=1)
    planning_model: Optional[str] = Field(None, min_length=1, max_length=128)
    planning_structure_version: int = Field(0, strict=True, ge=0, le=1)
    progression_arcs: List[StorySeedProgressionArc] = Field(default_factory=list)
    chapters: List[StorySeedStructuredChapter] = Field(..., min_length=1)
    thread_schedule_version: int = Field(0, strict=True, ge=0, le=1)
    thread_payoffs: List[StorySeedThreadPayoff] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_contiguous_positions(self):
        positions = [item.position for item in self.chapters]
        if positions != list(range(1, len(self.chapters) + 1)):
            raise ValueError("chapter positions must start at 1 and be contiguous")
        if self.planning_structure_version == 1:
            _validate_progression_arcs(self.progression_arcs, len(self.chapters))
        elif self.progression_arcs:
            raise ValueError("progression_arcs require planning_structure_version=1")
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


class StorySeedStructureRequest(BaseModel):
    chapter_count: Optional[int] = Field(None, strict=True, ge=1)
    model: Optional[str] = Field(None, min_length=1, max_length=128)


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


def _validate_progression_arcs(arcs, chapter_count: int) -> None:
    positions = [
        position
        for arc in arcs
        for position in range(arc.start_position, arc.end_position + 1)
    ]
    if positions != list(range(1, chapter_count + 1)):
        raise ValueError("progression arcs must cover all chapters contiguously")
    arc_ids = [arc.arc_id for arc in arcs]
    if len(arc_ids) != len(set(arc_ids)):
        raise ValueError("progression arc IDs must be unique")
    threads = [thread for arc in arcs for thread in arc.threads]
    thread_ids = [thread.thread_id for thread in threads]
    if len(thread_ids) != len(set(thread_ids)):
        raise ValueError("progression thread IDs must be unique")
    for thread in threads:
        if not 1 <= thread.open_position < thread.payoff_position <= chapter_count:
            raise ValueError(f"invalid progression thread range: {thread.thread_id}")
