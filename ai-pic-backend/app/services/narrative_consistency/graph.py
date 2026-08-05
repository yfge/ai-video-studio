from __future__ import annotations

import copy
from typing import Any

from .conditions import fact_is_active, matching_facts, resolve_selector
from .contracts import FactGraph
from .errors import GraphError
from .hashing import value_hash


def freeze_fact_graph(schema: dict, value: FactGraph | dict) -> dict:
    graph = FactGraph.model_validate(value).model_dump(exclude={"snapshot_hash"})
    validate_fact_graph(schema, graph)
    graph["snapshot_hash"] = graph_hash(graph)
    return graph


def graph_hash(graph: dict) -> str:
    return value_hash(
        {
            "schema": graph.get("schema"),
            "entities": graph.get("entities") or [],
            "facts": graph.get("facts") or [],
            "occurred_event_ids": graph.get("occurred_event_ids") or [],
        }
    )


def validate_fact_graph(schema: dict, graph: dict) -> None:
    types = {item["id"]: item for item in schema.get("entity_types") or []}
    predicates = {item["id"]: item for item in schema.get("predicates") or []}
    perspectives = {item["id"]: item for item in schema.get("perspectives") or []}
    entities = _unique(graph.get("entities") or [], "entity")
    evidence = _unique(graph.get("evidence") or [], "evidence")
    _unique(graph.get("facts") or [], "fact")
    for entity in entities.values():
        if entity["type_id"] not in types:
            raise GraphError(f"entity {entity['id']} has unknown type")
    for perspective in perspectives.values():
        holder = perspective.get("holder_entity_id")
        if holder and holder not in entities:
            raise GraphError(f"perspective {perspective['id']} has unknown holder")
    cardinality = set()
    for fact in graph.get("facts") or []:
        predicate = predicates.get(fact["predicate_id"])
        if not predicate:
            raise GraphError(f"fact {fact['id']} has unknown predicate")
        if predicate["persistence"] != "causal":
            raise GraphError(f"observation {predicate['id']} cannot enter fact graph")
        entity = entities.get(fact["subject_id"])
        if not entity or entity["type_id"] not in predicate["subject_type_ids"]:
            raise GraphError(f"fact {fact['id']} has invalid subject")
        _validate_scope(fact, perspectives)
        validate_value(predicate, fact.get("value"), entities)
        unknown_evidence = set(fact.get("evidence_ids") or []) - set(evidence)
        if unknown_evidence:
            raise GraphError(f"fact {fact['id']} has unknown evidence")
        if not predicate.get("temporal") and (
            fact.get("valid_from") or fact.get("valid_until")
        ):
            raise GraphError(f"fact {fact['id']} uses time on non-temporal predicate")
        if predicate["cardinality"] == "one" and not predicate.get("temporal"):
            key = _slot(fact)
            if key in cardinality:
                raise GraphError(f"single-valued fact slot is duplicated: {key}")
            cardinality.add(key)


def apply_effects(
    schema: dict,
    graph: dict,
    effects: list[dict],
    bindings: dict[str, list[str]],
    *,
    event_id: str,
    anchor_order: dict[str, int] | None = None,
) -> dict:
    result = copy.deepcopy(graph)
    predicates = {item["id"]: item for item in schema.get("predicates") or []}
    for index, effect in enumerate(effects, 1):
        predicate = predicates[effect["predicate_id"]]
        operation = effect["op"]
        scope = (
            "perspective"
            if operation in {"reveal", "conceal"}
            else effect.get("scope", "objective")
        )
        subject_id = resolve_selector(effect["subject"], bindings)
        selector = {
            "subject": subject_id,
            "predicate_id": predicate["id"],
            "scope": scope,
            "perspective_id": effect.get("perspective_id"),
        }
        value = _resolve_value(effect.get("value"), bindings)
        matches = matching_facts(selector, result, {})
        active_matches = [
            item
            for item in matches
            if fact_is_active(item, event_id if anchor_order else None, anchor_order)
        ]
        if operation == "retract":
            selected = [
                item
                for item in active_matches
                if "value" not in effect or item.get("value") == value
            ]
            _remove_or_expire(result, selected, predicate, effect, event_id)
            continue
        if operation == "assert" and active_matches:
            if any(item.get("value") == value for item in active_matches):
                continue
            if (
                predicate["mutability"] == "immutable"
                or predicate["cardinality"] == "one"
            ):
                raise GraphError(f"assert conflicts with existing {predicate['id']}")
        if operation == "reveal" and not _objective_fact(
            result,
            selector,
            value,
            event_id if anchor_order else None,
            anchor_order,
        ):
            raise GraphError(f"cannot reveal absent objective fact {predicate['id']}")
        if operation in {"replace", "reveal", "conceal"}:
            if predicate["mutability"] == "immutable" and active_matches:
                raise GraphError(
                    f"immutable predicate cannot be replaced: {predicate['id']}"
                )
            _remove_or_expire(result, active_matches, predicate, effect, event_id)
        validate_value(
            predicate,
            value,
            {item["id"]: item for item in result.get("entities") or []},
        )
        fact = {
            "id": effect.get("fact_id")
            or f"fact-{value_hash([event_id, index, selector, value])[:20]}",
            "subject_id": subject_id,
            "predicate_id": predicate["id"],
            "scope": scope,
            "perspective_id": effect.get("perspective_id"),
            "perspective_state": (
                "known"
                if operation == "reveal"
                else (
                    "hidden"
                    if operation == "conceal"
                    else effect.get("perspective_state")
                )
            ),
            "value": copy.deepcopy(value),
            "valid_from": effect.get("valid_from")
            or (event_id if predicate.get("temporal") else None),
            "valid_until": effect.get("valid_until"),
            "evidence_ids": list(effect.get("evidence_ids") or []),
        }
        result.setdefault("facts", []).append(fact)
    result["snapshot_hash"] = None
    return freeze_fact_graph(schema, result)


def validate_value(predicate: dict, value: Any, entities: dict[str, dict]) -> None:
    kind = predicate["value_kind"]
    valid = {
        "string": isinstance(value, str),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "json": value is not None,
        "entity_ref": isinstance(value, str) and value in entities,
        "enum": value in predicate.get("enum_values", []),
    }[kind]
    if not valid:
        raise GraphError(f"predicate {predicate['id']} received invalid {kind} value")
    if kind == "entity_ref":
        target_type = entities[value]["type_id"]
        if target_type not in predicate.get("value_entity_type_ids") or []:
            raise GraphError(
                f"predicate {predicate['id']} received invalid entity type"
            )


def _objective_fact(graph, selector, value, anchor, anchor_order) -> bool:
    objective = {**selector, "scope": "objective", "perspective_id": None}
    return any(
        item.get("value") == value
        for item in matching_facts(
            objective, graph, {}, anchor=anchor, anchor_order=anchor_order
        )
    )


def _resolve_value(value, bindings):
    if isinstance(value, dict) and set(value) == {"role"}:
        return resolve_selector(value, bindings)
    return value


def _remove_or_expire(result, matches, predicate, effect, event_id):
    if predicate.get("temporal"):
        until = effect.get("valid_until") or event_id
        for item in matches:
            item["valid_until"] = until
        return
    result["facts"] = [
        item for item in result.get("facts") or [] if item not in matches
    ]


def _validate_scope(fact, perspectives) -> None:
    if fact.get("scope", "objective") == "perspective":
        if fact.get("perspective_id") not in perspectives:
            raise GraphError(f"fact {fact['id']} has unknown perspective")
        if fact.get("perspective_state") not in {
            "known",
            "believed",
            "suspected",
            "hidden",
        }:
            raise GraphError(f"fact {fact['id']} has invalid perspective state")
    elif fact.get("perspective_id") or fact.get("perspective_state"):
        raise GraphError(f"objective fact {fact['id']} binds perspective metadata")


def _slot(fact) -> tuple:
    return (
        fact["subject_id"],
        fact["predicate_id"],
        fact.get("scope", "objective"),
        fact.get("perspective_id"),
    )


def _unique(rows, label: str):
    result = {item["id"]: item for item in rows}
    if len(result) != len(rows):
        raise GraphError(f"duplicate {label} id")
    return result
