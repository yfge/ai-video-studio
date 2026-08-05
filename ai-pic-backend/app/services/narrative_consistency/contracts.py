from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class EntityType(BaseModel):
    id: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    capabilities: list[str] = Field(default_factory=list)


class Predicate(BaseModel):
    id: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    subject_type_ids: list[str] = Field(..., min_length=1)
    value_kind: Literal["string", "number", "boolean", "entity_ref", "enum", "json"]
    value_entity_type_ids: list[str] = Field(default_factory=list)
    enum_values: list[Any] = Field(default_factory=list)
    cardinality: Literal["one", "many"] = "one"
    mutability: Literal["immutable", "replaceable", "accumulative"] = "replaceable"
    temporal: bool = False
    persistence: Literal["causal", "observational"] = "causal"


class Perspective(BaseModel):
    id: str = Field(..., min_length=1)
    kind: Literal["holder", "audience"]
    holder_entity_id: str | None = None

    @model_validator(mode="after")
    def require_holder(self):
        if self.kind == "holder" and not self.holder_entity_id:
            raise ValueError("holder perspective requires holder_entity_id")
        return self


class EventType(BaseModel):
    id: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    roles: dict[str, list[str]] = Field(default_factory=dict)
    preconditions: list[dict[str, Any]] = Field(default_factory=list)
    effects: list[dict[str, Any]] = Field(default_factory=list)
    repeatable: bool = False


class Constraint(BaseModel):
    id: str = Field(..., min_length=1)
    kind: Literal["invariant", "mutual_exclusion", "unique", "order", "dependency"]
    expression: dict[str, Any]
    severity: Literal["blocking", "warning"] = "blocking"


class ConsistencySchema(BaseModel):
    schema: Literal["story_novel_consistency_schema.v1"]
    version: int = Field(1, ge=1)
    entity_types: list[EntityType] = Field(default_factory=list)
    predicates: list[Predicate] = Field(default_factory=list)
    event_types: list[EventType] = Field(default_factory=list)
    constraints: list[Constraint] = Field(default_factory=list)
    perspectives: list[Perspective] = Field(default_factory=list)
    source_manifest: dict[str, Any] = Field(default_factory=dict)
    schema_hash: str | None = None


class Entity(BaseModel):
    id: str = Field(..., min_length=1)
    type_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    aliases: list[str] = Field(default_factory=list)


class Evidence(BaseModel):
    id: str = Field(..., min_length=1)
    source_artifact_type: str = Field(..., min_length=1)
    source_artifact_id: str = Field(..., min_length=1)
    source_version: int = Field(..., ge=1)
    source_hash: str = Field(..., min_length=1)
    sentence_ids: list[str] = Field(..., min_length=1)
    quote: str = Field(..., min_length=1)


class Fact(BaseModel):
    id: str = Field(..., min_length=1)
    subject_id: str = Field(..., min_length=1)
    predicate_id: str = Field(..., min_length=1)
    value: Any
    scope: Literal["objective", "perspective"] = "objective"
    perspective_id: str | None = None
    perspective_state: Literal["known", "believed", "suspected", "hidden"] | None = None
    valid_from: str | None = None
    valid_until: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_perspective(self):
        if self.scope == "perspective" and not self.perspective_id:
            raise ValueError("perspective fact requires perspective_id")
        if self.scope == "perspective" and not self.perspective_state:
            raise ValueError("perspective fact requires perspective_state")
        if self.scope == "objective" and (
            self.perspective_id or self.perspective_state
        ):
            raise ValueError("objective fact cannot bind perspective metadata")
        return self


class FactGraph(BaseModel):
    schema: Literal["story_novel_fact_graph.v1"]
    entities: list[Entity] = Field(default_factory=list)
    facts: list[Fact] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    occurred_event_ids: list[str] = Field(default_factory=list)
    snapshot_hash: str | None = None


class NarrativeObligation(BaseModel):
    id: str = Field(..., min_length=1)
    kind: Literal["setup", "payoff", "arc", "scene", "hook"]
    chapter_position: int = Field(..., ge=1)
    required_event_ids: list[str] = Field(default_factory=list)


class CausalEvent(BaseModel):
    id: str = Field(..., min_length=1)
    event_type_id: str = Field(..., min_length=1)
    chapter_position: int = Field(..., ge=1)
    role_bindings: dict[str, list[str]] = Field(default_factory=dict)
    dependency_event_ids: list[str] = Field(default_factory=list)
    preconditions: list[dict[str, Any]] = Field(default_factory=list)
    effects: list[dict[str, Any]] = Field(default_factory=list)
    obligation_ids: list[str] = Field(default_factory=list)


class CausalEventGraph(BaseModel):
    schema: Literal["story_novel_causal_event_graph.v1"]
    events: list[CausalEvent] = Field(default_factory=list)
    obligations: list[NarrativeObligation] = Field(default_factory=list)
    graph_hash: str | None = None


class Claim(BaseModel):
    id: str = Field(..., min_length=1)
    operation: Literal["assert", "retract", "replace"]
    subject_id: str = Field(..., min_length=1)
    predicate_id: str = Field(..., min_length=1)
    value: Any
    scope: Literal["objective", "perspective"] = "objective"
    perspective_id: str | None = None
    perspective_state: Literal["known", "believed", "suspected", "hidden"] | None = None
    source_event_id: str | None = None
    valid_from: str | None = None
    valid_until: str | None = None
    evidence_ids: list[str] = Field(..., min_length=1)


class ObservedEvent(BaseModel):
    id: str = Field(..., min_length=1)
    event_type_id: str = Field(..., min_length=1)
    role_bindings: dict[str, list[str]] = Field(default_factory=dict)
    evidence_ids: list[str] = Field(..., min_length=1)


class ClaimDelta(BaseModel):
    schema: Literal["story_novel_claim_delta.v1"]
    claims: list[Claim] = Field(default_factory=list)
    perspective_changes: list[Claim] = Field(default_factory=list)
    occurred_events: list[ObservedEvent] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
