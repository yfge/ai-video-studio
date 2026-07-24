"""Structured contracts for outline-driven long-form novel generation."""

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class StoryNovelCanonTimelineEvent(BaseModel):
    id: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    order: int
    story_time: str = Field(..., min_length=1)
    immutable: bool = True
    source_chapter_position: int | None = Field(default=None, ge=1)
    source_key_event: str | None = Field(default=None, min_length=1)


class StoryNovelCanonEntity(BaseModel):
    id: str = Field(..., min_length=1)
    kind: Literal["character", "location", "object", "organization"]
    name: str = Field(..., min_length=1)
    aliases: list[str] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)


class StoryNovelCanonRule(BaseModel):
    id: str = Field(..., min_length=1)
    statement: str = Field(..., min_length=1)
    exceptions: list[str] = Field(default_factory=list)


class StoryNovelMilestoneOutcome(BaseModel):
    subject_id: str = Field(..., min_length=1)
    field: str = Field(..., min_length=1)
    operator: Literal["eq", "contains"] = "eq"
    value: Any


class StoryNovelCanonMilestone(BaseModel):
    id: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    planned_position: int | None = Field(default=None, ge=1)
    repeatable: bool = False
    outcomes: list[StoryNovelMilestoneOutcome] = Field(default_factory=list)


class StoryNovelCanonArcCheckpoint(BaseModel):
    position: int = Field(..., ge=1)
    state: str = Field(..., min_length=1)


class StoryNovelCanonCharacterArc(BaseModel):
    character_id: str = Field(..., min_length=1)
    start_state: str = Field(..., min_length=1)
    checkpoints: list[StoryNovelCanonArcCheckpoint] = Field(default_factory=list)
    end_state: str = Field(..., min_length=1)


class StoryNovelCanon(BaseModel):
    gate_version: int = Field(0, ge=0)
    timeline: list[StoryNovelCanonTimelineEvent] = Field(default_factory=list)
    entities: list[StoryNovelCanonEntity] = Field(default_factory=list)
    world_rules: list[StoryNovelCanonRule] = Field(default_factory=list)
    milestones: list[StoryNovelCanonMilestone] = Field(default_factory=list)
    character_arcs: list[StoryNovelCanonCharacterArc] = Field(default_factory=list)
    initial_state: dict[str, dict[str, Any]] = Field(default_factory=dict)
    canon_hash: str | None = None


class StoryNovelStatePredicate(BaseModel):
    subject_id: str = Field(..., min_length=1)
    field: str = Field(..., min_length=1)
    operator: Literal["eq", "ne", "contains", "not_contains"] = "eq"
    value: Any


class StoryNovelStateTransition(BaseModel):
    subject_id: str = Field(..., min_length=1)
    field: str = Field(..., min_length=1)
    from_value: Any = None
    to_value: Any
    reason: str = ""


class StoryNovelKnowledgeGrant(BaseModel):
    character_id: str = Field(..., min_length=1)
    fact_id: str = Field(..., min_length=1)
    source_event_id: str = Field(..., min_length=1)


class StoryNovelLocationTransition(BaseModel):
    subject_id: str = Field(..., min_length=1)
    from_location_id: str | None = Field(..., min_length=1)
    to_location_id: str = Field(..., min_length=1)
    means: str = Field(..., min_length=1)


class StoryNovelChapterPlan(BaseModel):
    position: int = Field(..., ge=1)
    title: str = Field(..., min_length=1, max_length=255)
    goal: str = Field(..., min_length=1)
    key_events: list[str] = Field(..., min_length=1)
    character_focus: list[str] = Field(default_factory=list)
    open_threads: list[str] = Field(default_factory=list)
    end_state: str = Field(..., min_length=1)
    min_chars: int = Field(3000, strict=True, gt=0)
    target_chars: int = Field(..., strict=True, gt=0)
    max_chars: int = Field(5000, strict=True, gt=0)
    length_source: Literal["profile_default", "chapter_override"] = "profile_default"
    preconditions: list[StoryNovelStatePredicate] = Field(default_factory=list)
    required_event_ids: list[str] = Field(default_factory=list)
    state_transitions: list[StoryNovelStateTransition] = Field(default_factory=list)
    knowledge_grants: list[StoryNovelKnowledgeGrant] = Field(default_factory=list)
    location_transitions: list[StoryNovelLocationTransition] = Field(
        default_factory=list
    )
    milestones_consumed: list[str] = Field(default_factory=list)
    forbidden_event_ids: list[str] = Field(default_factory=list)
    payoffs_due: list[str] = Field(default_factory=list)
    canon_refs: list[str] = Field(default_factory=list)
    timeline_event_bindings: dict[str, str]

    @model_validator(mode="after")
    def require_finite_length_range(self):
        if any(not item.strip() for item in self.required_event_ids):
            raise ValueError("required_event_ids must contain non-blank IDs")
        if any(
            not timeline_id.strip() or not event_id.strip()
            for timeline_id, event_id in self.timeline_event_bindings.items()
        ):
            raise ValueError(
                "timeline_event_bindings must contain non-blank timeline and event IDs"
            )
        if not self.min_chars <= self.target_chars <= self.max_chars:
            raise ValueError(
                "chapter length must satisfy min_chars <= target_chars <= max_chars"
            )
        return self


class StoryNovelGenerationPlan(BaseModel):
    chapters: list[StoryNovelChapterPlan] = Field(..., min_length=1)

    @model_validator(mode="after")
    def require_contiguous_positions(self):
        positions = [item.position for item in self.chapters]
        if positions != list(range(1, len(self.chapters) + 1)):
            raise ValueError("chapter positions must start at 1 and be contiguous")
        return self


class StoryNovelPlotDelta(BaseModel):
    key_events: list[str] = Field(default_factory=list)
    unresolved_threads: list[str] = Field(default_factory=list)
    resolved_threads: list[str] = Field(default_factory=list)
    character_states: dict[str, Any] = Field(default_factory=dict)


class StoryNovelStateDelta(BaseModel):
    occurred_event_ids: list[str] = Field(default_factory=list)
    premature_future_event_ids: list[str] = Field(default_factory=list)
    future_event_audit: dict[str, Literal["not_present", "premature"]] = Field(
        default_factory=dict
    )
    state_transitions: list[StoryNovelStateTransition] = Field(default_factory=list)
    knowledge_grants: list[StoryNovelKnowledgeGrant] = Field(default_factory=list)
    location_transitions: list[StoryNovelLocationTransition] = Field(
        default_factory=list
    )
    milestones_consumed: list[str] = Field(default_factory=list)
    opened_thread_ids: list[str] = Field(default_factory=list)
    resolved_thread_ids: list[str] = Field(default_factory=list)
    world_rule_violations: list[str] = Field(default_factory=list)
    evidence: dict[str, str] = Field(default_factory=dict)
    timeline_evidence: dict[str, str] = Field(default_factory=dict)


class StoryNovelChapterGeneration(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content_text: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    cliffhanger: str | None = None
    plot_delta: StoryNovelPlotDelta = Field(default_factory=StoryNovelPlotDelta)
