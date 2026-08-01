"""Genre-neutral character roadmap and world-scope contracts for StorySeed."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator


class StorySeedCoreCharacterRoute(BaseModel):
    character_ref: str = Field(..., min_length=1)
    narrative_function: str = Field(..., min_length=1)
    first_allowed_position: int = Field(..., strict=True, ge=1)
    planned_arc_id: str = Field(..., min_length=1)
    relationship_targets: list[str] = Field(default_factory=list)
    start_direction: str = Field(..., min_length=1)
    turning_directions: list[str] = Field(default_factory=list)
    terminal_direction: str = Field(..., min_length=1)
    hidden_state: dict[str, Any] = Field(default_factory=dict)


class StorySeedCharacterSlot(BaseModel):
    slot_id: str = Field(..., min_length=1)
    narrative_function: str = Field(..., min_length=1)
    relationship_target: Optional[str] = Field(None, min_length=1)
    entrance_preconditions: list[str] = Field(default_factory=list)
    required_capabilities: list[str] = Field(default_factory=list)
    mandatory: bool = False


class StorySeedScopeType(BaseModel):
    type_id: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    parent_type_id: Optional[str] = Field(None, min_length=1)


class StorySeedScopeNode(BaseModel):
    scope_id: str = Field(..., min_length=1)
    scope_type: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    parent_scope_id: Optional[str] = Field(None, min_length=1)
    depth: int = Field(0, strict=True, ge=0)
    first_allowed_position: int = Field(1, strict=True, ge=1)
    visibility: Literal["hidden", "known", "visited"] = "known"
    governing_entities: list[str] = Field(default_factory=list)
    local_rules: list[str] = Field(default_factory=list)
    state: dict[str, Any] = Field(default_factory=dict)


class StorySeedScopeEdge(BaseModel):
    edge_id: str = Field(..., min_length=1)
    from_scope_id: str = Field(..., min_length=1)
    to_scope_id: str = Field(..., min_length=1)
    connection_type: str = Field(..., min_length=1)
    direction: Literal["one_way", "two_way"] = "two_way"
    cost: dict[str, Any] = Field(default_factory=dict)
    duration: dict[str, Any] = Field(default_factory=dict)
    preconditions: list[str] = Field(default_factory=list)
    available_from_position: int = Field(1, strict=True, ge=1)


class StorySeedScopeSlot(BaseModel):
    slot_id: str = Field(..., min_length=1)
    narrative_function: str = Field(..., min_length=1)
    parent_scope_id: Optional[str] = Field(None, min_length=1)
    scale_direction: Literal["deeper", "broader", "parallel", "higher"]
    entrance_preconditions: list[str] = Field(default_factory=list)
    mandatory: bool = False


class StorySeedWorldRoadmap(BaseModel):
    core_character_routes: list[StorySeedCoreCharacterRoute] = Field(
        default_factory=list
    )
    scope_taxonomy: list[StorySeedScopeType] = Field(default_factory=list)
    initial_scope_nodes: list[StorySeedScopeNode] = Field(default_factory=list)
    initial_scope_edges: list[StorySeedScopeEdge] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_graph(self):
        type_ids = _unique([item.type_id for item in self.scope_taxonomy], "scope type")
        for item in self.scope_taxonomy:
            if item.parent_type_id and item.parent_type_id not in type_ids:
                raise ValueError(f"unknown parent scope type: {item.parent_type_id}")
        node_ids = _unique(
            [item.scope_id for item in self.initial_scope_nodes], "scope"
        )
        for item in self.initial_scope_nodes:
            if type_ids and item.scope_type not in type_ids:
                raise ValueError(f"unknown scope type: {item.scope_type}")
            if item.parent_scope_id and item.parent_scope_id not in node_ids:
                raise ValueError(f"unknown parent scope: {item.parent_scope_id}")
        _validate_acyclic(self.initial_scope_nodes)
        _validate_depths(self.initial_scope_nodes)
        _unique([item.edge_id for item in self.initial_scope_edges], "scope edge")
        for item in self.initial_scope_edges:
            if item.from_scope_id not in node_ids or item.to_scope_id not in node_ids:
                raise ValueError(f"scope edge endpoint is unknown: {item.edge_id}")
        return self


def require_v4_roots(roadmap: StorySeedWorldRoadmap) -> None:
    """Reject a v4 roadmap that has no durable cast or opening world."""
    if not roadmap.core_character_routes:
        raise ValueError("v4 roadmap requires core character routes")
    if not roadmap.scope_taxonomy:
        raise ValueError("v4 roadmap requires a scope taxonomy")
    if not roadmap.initial_scope_nodes:
        raise ValueError("v4 roadmap requires initial scope nodes")


def _unique(values: list[str], label: str) -> set[str]:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} IDs must be unique")
    return set(values)


def _validate_acyclic(nodes: list[StorySeedScopeNode]) -> None:
    parents = {item.scope_id: item.parent_scope_id for item in nodes}
    for node_id in parents:
        seen, current = set(), node_id
        while current:
            if current in seen:
                raise ValueError(f"scope hierarchy contains cycle: {node_id}")
            seen.add(current)
            current = parents.get(current)


def _validate_depths(nodes: list[StorySeedScopeNode]) -> None:
    values = {item.scope_id: item for item in nodes}
    for item in nodes:
        expected = values[item.parent_scope_id].depth + 1 if item.parent_scope_id else 0
        if item.depth != expected:
            raise ValueError(f"scope depth does not match parent: {item.scope_id}")
