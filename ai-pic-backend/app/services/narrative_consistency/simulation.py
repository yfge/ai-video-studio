from __future__ import annotations

import copy

from .conditions import condition_matches
from .constraints import (
    validate_graph_constraints,
    validate_order_constraints,
    validate_temporal_anchors,
)
from .contracts import CausalEventGraph
from .errors import GraphError
from .graph import apply_effects, freeze_fact_graph
from .hashing import value_hash
from .schema import validate_condition, validate_effect


def freeze_causal_graph(schema: dict, value: CausalEventGraph | dict) -> dict:
    graph = CausalEventGraph.model_validate(value).model_dump(exclude={"graph_hash"})
    validate_causal_graph(schema, graph)
    graph["graph_hash"] = value_hash(graph)
    return graph


def validate_causal_graph(schema: dict, graph: dict) -> None:
    event_types = {item["id"]: item for item in schema.get("event_types") or []}
    predicates = {item["id"]: item for item in schema.get("predicates") or []}
    perspectives = {item["id"] for item in schema.get("perspectives") or []}
    events = _unique(graph.get("events") or [], "event")
    obligations = _unique(graph.get("obligations") or [], "obligation")
    for event in events.values():
        event_type = event_types.get(event["event_type_id"])
        if not event_type:
            raise GraphError(f"event {event['id']} has unknown type")
        _validate_bindings(event, event_type)
        unknown_dependencies = set(event["dependency_event_ids"]) - set(events)
        if unknown_dependencies:
            raise GraphError(f"event {event['id']} has unknown dependencies")
        unknown_obligations = set(event["obligation_ids"]) - set(obligations)
        if unknown_obligations:
            raise GraphError(f"event {event['id']} has unknown obligations")
        roles = set(event_type.get("roles") or {})
        for rule in [*event_type["preconditions"], *event["preconditions"]]:
            validate_condition(rule, predicates, roles, perspectives)
        for effect in [*event_type["effects"], *event["effects"]]:
            validate_effect(effect, predicates, roles, perspectives)
        for dependency in event["dependency_event_ids"]:
            if events[dependency]["chapter_position"] > event["chapter_position"]:
                raise GraphError(f"event {event['id']} depends on a future chapter")
    for obligation in obligations.values():
        unknown = set(obligation["required_event_ids"]) - set(events)
        if unknown:
            raise GraphError(f"obligation {obligation['id']} has unknown events")
        if not obligation["required_event_ids"] or any(
            events[event_id]["chapter_position"] != obligation["chapter_position"]
            for event_id in obligation["required_event_ids"]
        ):
            raise GraphError(
                f"obligation {obligation['id']} must bind events in its chapter"
            )
        if any(
            obligation["id"] not in events[event_id]["obligation_ids"]
            for event_id in obligation["required_event_ids"]
        ):
            raise GraphError(f"obligation {obligation['id']} is not event-bound")
    _topological_events(events)
    validate_order_constraints(schema, events)


def simulate_causal_graph(
    schema: dict, initial_graph: dict, causal_graph: dict
) -> dict:
    frozen = freeze_causal_graph(schema, causal_graph)
    events = {item["id"]: item for item in frozen["events"]}
    current = freeze_fact_graph(schema, initial_graph)
    ordered = _topological_events(events)
    anchor_order = {item["id"]: index for index, item in enumerate(ordered)}
    validate_temporal_anchors(current, anchor_order)
    if ordered:
        validate_graph_constraints(
            schema,
            current,
            events,
            anchor=ordered[0]["id"],
            anchor_order=anchor_order,
        )
    snapshots = []
    for event in ordered:
        event_type = next(
            item
            for item in schema["event_types"]
            if item["id"] == event["event_type_id"]
        )
        _validate_runtime_bindings(current, event, event_type)
        rules = [*event_type.get("preconditions", []), *event["preconditions"]]
        failed = [
            rule
            for rule in rules
            if not condition_matches(
                rule,
                current,
                event["role_bindings"],
                anchor=event["id"],
                anchor_order=anchor_order,
            )
        ]
        if failed:
            raise GraphError(f"event {event['id']} preconditions are not satisfied")
        effects = [*event_type.get("effects", []), *event["effects"]]
        current = apply_effects(
            schema,
            current,
            effects,
            event["role_bindings"],
            event_id=event["id"],
            anchor_order=anchor_order,
        )
        occurred = list(current.get("occurred_event_ids") or [])
        occurred.append(event["id"])
        current["occurred_event_ids"] = occurred
        current = freeze_fact_graph(schema, current)
        validate_temporal_anchors(current, anchor_order)
        validate_graph_constraints(
            schema,
            current,
            events,
            anchor=event["id"],
            anchor_order=anchor_order,
        )
        snapshots.append(
            {
                "event_id": event["id"],
                "chapter_position": event["chapter_position"],
                "snapshot_hash": current["snapshot_hash"],
            }
        )
    return {
        "status": "passed",
        "causal_graph_hash": frozen["graph_hash"],
        "snapshots": snapshots,
        "final_graph": current,
    }


def _validate_bindings(event, event_type) -> None:
    allowed_roles = event_type.get("roles") or {}
    if set(event["role_bindings"]) != set(allowed_roles):
        raise GraphError(f"event {event['id']} role bindings are incomplete")
    for role, values in event["role_bindings"].items():
        if not values or len(values) != len(set(values)):
            raise GraphError(f"event {event['id']} role {role} is empty or duplicated")


def _validate_runtime_bindings(graph, event, event_type) -> None:
    entities = {item["id"]: item for item in graph.get("entities") or []}
    for role, entity_ids in event["role_bindings"].items():
        allowed_types = set(event_type["roles"][role])
        if any(
            value not in entities or entities[value]["type_id"] not in allowed_types
            for value in entity_ids
        ):
            raise GraphError(f"event {event['id']} role {role} has invalid entities")


def _topological_events(events: dict[str, dict]) -> list[dict]:
    pending = copy.deepcopy(events)
    completed = set()
    result = []
    while pending:
        ready = [
            item
            for item in pending.values()
            if set(item["dependency_event_ids"]).issubset(completed)
        ]
        if not ready:
            raise GraphError("causal event graph contains a dependency cycle")
        ready.sort(key=lambda item: (item["chapter_position"], item["id"]))
        for item in ready:
            result.append(item)
            completed.add(item["id"])
            pending.pop(item["id"])
    return result


def _unique(rows, label):
    result = {item["id"]: item for item in rows}
    if len(result) != len(rows):
        raise GraphError(f"duplicate {label} id")
    return result
