from __future__ import annotations

from .claims import validate_claim_delta
from .conditions import condition_matches
from .constraints import validate_graph_constraints, validate_temporal_anchors
from .errors import GraphError
from .graph import apply_effects, freeze_fact_graph


def validate_chapter_transition(
    schema: dict,
    graph: dict,
    delta: dict,
    sentence_index: list[dict],
    *,
    allowed_event_ids: set[str],
    event_catalog: dict[str, dict],
) -> dict:
    observed = {item.get("id") for item in delta.get("occurred_events") or []}
    if observed != allowed_event_ids:
        raise GraphError(
            f"chapter events mismatch: expected={sorted(allowed_event_ids)} "
            f"observed={sorted(item for item in observed if item)}"
        )
    anchor_order = _event_order(event_catalog)
    expected, current_anchor = _apply_planned_events(
        schema, graph, allowed_event_ids, event_catalog, delta
    )
    actual = validate_claim_delta(
        schema,
        graph,
        delta,
        sentence_index,
        allowed_event_ids=allowed_event_ids,
        event_catalog=event_catalog,
        current_anchor=current_anchor,
        anchor_order=anchor_order,
    )
    if _semantic_facts(expected) != _semantic_facts(actual["graph_after"]):
        raise GraphError("extracted causal claims do not match planned event effects")
    return actual


def _apply_planned_events(schema, graph, allowed, catalog, delta):
    current = freeze_fact_graph(schema, graph)
    observed = {item["id"]: item for item in delta.get("occurred_events") or []}
    pending = {event_id: catalog[event_id] for event_id in allowed}
    event_types = {item["id"]: item for item in schema.get("event_types") or []}
    anchor_order = _event_order(catalog)
    current_anchor = None
    while pending:
        occurred = set(current.get("occurred_event_ids") or [])
        ready = [
            item
            for item in pending.values()
            if set(item.get("dependency_event_ids") or []).issubset(
                occurred | (allowed - set(pending))
            )
        ]
        if not ready:
            raise GraphError("chapter events have unsatisfied dependencies")
        ready.sort(key=lambda item: item["id"])
        for event in ready:
            actual = observed[event["id"]]
            if actual.get("role_bindings") != event.get("role_bindings"):
                raise GraphError(f"event {event['id']} role bindings changed in prose")
            event_type = event_types[event["event_type_id"]]
            rules = [
                *event_type.get("preconditions", []),
                *event.get("preconditions", []),
            ]
            if any(
                not condition_matches(
                    rule,
                    current,
                    event["role_bindings"],
                    anchor=event["id"],
                    anchor_order=anchor_order,
                )
                for rule in rules
            ):
                raise GraphError(f"event {event['id']} preconditions are not satisfied")
            effects = [*event_type.get("effects", []), *event.get("effects", [])]
            current = apply_effects(
                schema,
                current,
                effects,
                event["role_bindings"],
                event_id=event["id"],
                anchor_order=anchor_order,
            )
            current["occurred_event_ids"] = [
                *current.get("occurred_event_ids", []),
                event["id"],
            ]
            current = freeze_fact_graph(schema, current)
            current_anchor = event["id"]
            validate_temporal_anchors(current, anchor_order)
            pending.pop(event["id"])
    validate_graph_constraints(
        schema,
        current,
        anchor=current_anchor,
        anchor_order=anchor_order,
    )
    return current, current_anchor


def _semantic_facts(graph):
    keys = (
        "subject_id",
        "predicate_id",
        "value",
        "scope",
        "perspective_id",
        "perspective_state",
        "valid_from",
        "valid_until",
    )
    return sorted(
        [
            tuple(repr(item.get(key)) for key in keys)
            for item in graph.get("facts") or []
        ]
    )


def _event_order(catalog):
    pending = {key: value for key, value in catalog.items()}
    completed, result = set(), []
    while pending:
        ready = [
            item
            for item in pending.values()
            if set(item.get("dependency_event_ids") or []).issubset(completed)
        ]
        if not ready:
            raise GraphError("event catalog contains a dependency cycle")
        ready.sort(key=lambda item: (item["chapter_position"], item["id"]))
        for item in ready:
            result.append(item["id"])
            completed.add(item["id"])
            pending.pop(item["id"])
    return {event_id: index for index, event_id in enumerate(result)}
