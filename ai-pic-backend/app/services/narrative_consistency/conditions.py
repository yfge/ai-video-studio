from __future__ import annotations

from typing import Any

from .errors import GraphError


def condition_matches(
    rule: dict,
    graph: dict,
    bindings: dict[str, list[str]],
    *,
    anchor: str | None = None,
    anchor_order: dict[str, int] | None = None,
) -> bool:
    op = rule["op"]
    if op == "all":
        return all(
            condition_matches(
                item, graph, bindings, anchor=anchor, anchor_order=anchor_order
            )
            for item in rule["args"]
        )
    if op == "any":
        return any(
            condition_matches(
                item, graph, bindings, anchor=anchor, anchor_order=anchor_order
            )
            for item in rule["args"]
        )
    if op == "not":
        return not condition_matches(
            rule["arg"], graph, bindings, anchor=anchor, anchor_order=anchor_order
        )
    if op == "event_before":
        return rule["event_id"] in (graph.get("occurred_event_ids") or [])
    facts = matching_facts(
        rule, graph, bindings, anchor=anchor, anchor_order=anchor_order
    )
    if op == "exists":
        return bool(facts)
    expected = _resolve_value(rule.get("value"), bindings)
    if op == "equals":
        return any(item.get("value") == expected for item in facts)
    return any(_contains(item.get("value"), expected) for item in facts)


def matching_facts(
    rule: dict,
    graph: dict,
    bindings: dict[str, list[str]],
    *,
    anchor: str | None = None,
    anchor_order: dict[str, int] | None = None,
) -> list[dict]:
    subject = resolve_selector(rule["subject"], bindings)
    scope = rule.get("scope", "objective")
    perspective_id = rule.get("perspective_id")
    return [
        item
        for item in graph.get("facts") or []
        if item.get("subject_id") == subject
        and item.get("predicate_id") == rule.get("predicate_id")
        and item.get("scope", "objective") == scope
        and item.get("perspective_id") == perspective_id
        and fact_is_active(item, anchor, anchor_order)
    ]


def resolve_selector(value: Any, bindings: dict[str, list[str]]) -> str:
    if isinstance(value, str):
        return value
    role = str((value or {}).get("role") or "")
    rows = list(bindings.get(role) or [])
    if len(rows) != 1:
        raise GraphError(f"role {role} must bind exactly one entity")
    return rows[0]


def _resolve_value(value: Any, bindings: dict[str, list[str]]):
    if isinstance(value, dict) and set(value) == {"role"}:
        return resolve_selector(value, bindings)
    return value


def _contains(container, expected) -> bool:
    if isinstance(container, (list, tuple, set, str, dict)):
        return expected in container
    return False


def fact_is_active(fact, anchor, order) -> bool:
    if anchor is None:
        return True
    if order is None or anchor not in order:
        raise GraphError(f"unknown temporal evaluation anchor: {anchor}")
    current = order[anchor]
    valid_from = fact.get("valid_from")
    valid_until = fact.get("valid_until")
    if valid_from and (valid_from not in order or current < order[valid_from]):
        return False
    if valid_until and (valid_until not in order or current >= order[valid_until]):
        return False
    return True
