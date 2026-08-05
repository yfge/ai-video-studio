from __future__ import annotations

from .conditions import condition_matches, fact_is_active
from .errors import GraphError


def validate_graph_constraints(
    schema, graph, events=None, *, anchor=None, anchor_order=None
) -> None:
    events = events or {}
    _validate_active_cardinality(schema, graph, anchor, anchor_order)
    for constraint in schema.get("constraints") or []:
        if constraint.get("severity") != "blocking":
            continue
        kind = constraint["kind"]
        expression = constraint["expression"]
        if kind == "invariant" and not condition_matches(
            expression, graph, {}, anchor=anchor, anchor_order=anchor_order
        ):
            raise GraphError(f"invariant failed: {constraint['id']}")
        if kind == "mutual_exclusion":
            hits = sum(
                condition_matches(
                    item, graph, {}, anchor=anchor, anchor_order=anchor_order
                )
                for item in expression.get("conditions") or []
            )
            if hits > 1:
                raise GraphError(f"mutual exclusion failed: {constraint['id']}")
        if kind == "unique":
            values = [
                item.get("value")
                for item in graph.get("facts") or []
                if item.get("predicate_id") == expression["predicate_id"]
                and fact_is_active(item, anchor, anchor_order)
            ]
            if len(values) != len({repr(item) for item in values}):
                raise GraphError(f"unique constraint failed: {constraint['id']}")


def validate_order_constraints(schema, events) -> None:
    for constraint in schema.get("constraints") or []:
        if constraint["kind"] not in {"order", "dependency"}:
            continue
        expression = constraint["expression"]
        before = events.get(expression["before_event_id"])
        after = events.get(expression["after_event_id"])
        if not before or not after:
            raise GraphError(f"constraint {constraint['id']} references unknown events")
        if (
            constraint["kind"] == "order"
            and before["chapter_position"] > after["chapter_position"]
        ):
            raise GraphError(f"order constraint failed: {constraint['id']}")
        if (
            constraint["kind"] == "order"
            and before["chapter_position"] == after["chapter_position"]
            and not _depends_on(after["id"], before["id"], events)
        ):
            raise GraphError(f"order constraint failed: {constraint['id']}")
        if (
            constraint["kind"] == "dependency"
            and before["id"] not in after["dependency_event_ids"]
        ):
            raise GraphError(f"dependency constraint failed: {constraint['id']}")


def _depends_on(event_id, expected, events):
    pending = list((events.get(event_id) or {}).get("dependency_event_ids") or [])
    seen = set()
    while pending:
        current = pending.pop()
        if current == expected:
            return True
        if current in seen:
            continue
        seen.add(current)
        pending.extend((events.get(current) or {}).get("dependency_event_ids") or [])
    return False


def validate_temporal_anchors(graph, anchor_order):
    for fact in graph.get("facts") or []:
        for field in ("valid_from", "valid_until"):
            value = fact.get(field)
            if value and value not in anchor_order:
                raise GraphError(f"fact {fact['id']} has unknown {field}: {value}")
        start, end = fact.get("valid_from"), fact.get("valid_until")
        if start and end and anchor_order[start] >= anchor_order[end]:
            raise GraphError(f"fact {fact['id']} has an empty temporal range")


def _validate_active_cardinality(schema, graph, anchor, anchor_order):
    predicates = {item["id"]: item for item in schema.get("predicates") or []}
    slots = set()
    for fact in graph.get("facts") or []:
        predicate = predicates.get(fact.get("predicate_id")) or {}
        if predicate.get("cardinality") != "one" or not fact_is_active(
            fact, anchor, anchor_order
        ):
            continue
        slot = (
            fact.get("subject_id"),
            fact.get("predicate_id"),
            fact.get("scope", "objective"),
            fact.get("perspective_id"),
        )
        if slot in slots:
            raise GraphError(f"single-valued fact slot is duplicated: {slot}")
        slots.add(slot)
