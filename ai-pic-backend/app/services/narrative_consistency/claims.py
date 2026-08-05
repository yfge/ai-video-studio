from __future__ import annotations

from .contracts import ClaimDelta
from .constraints import validate_graph_constraints
from .errors import GraphError
from .evidence import validate_evidence
from .graph import apply_effects, freeze_fact_graph, validate_value
from .hashing import value_hash


def validate_claim_delta(
    schema: dict,
    graph: dict,
    delta_value: ClaimDelta | dict,
    sentence_index: list[dict],
    *,
    allowed_event_ids: set[str],
    event_catalog: dict[str, dict],
    current_anchor: str | None = None,
    anchor_order: dict[str, int] | None = None,
) -> dict:
    delta = ClaimDelta.model_validate(delta_value).model_dump()
    validate_evidence(delta["evidence"], sentence_index)
    evidence_ids = {item["id"] for item in delta["evidence"]}
    entities = {item["id"]: item for item in graph.get("entities") or []}
    predicates = {item["id"]: item for item in schema.get("predicates") or []}
    perspectives = {item["id"] for item in schema.get("perspectives") or []}
    causal, observations = [], []
    for claim in [*delta["claims"], *delta["perspective_changes"]]:
        predicate = predicates.get(claim["predicate_id"])
        if not predicate:
            raise GraphError(f"claim {claim['id']} has unknown predicate")
        entity = entities.get(claim["subject_id"])
        if not entity or entity["type_id"] not in predicate["subject_type_ids"]:
            raise GraphError(f"claim {claim['id']} has invalid subject")
        if claim["scope"] == "perspective":
            if claim.get("perspective_id") not in perspectives:
                raise GraphError(f"claim {claim['id']} has unknown perspective")
            if claim.get("perspective_state") not in {
                "known",
                "believed",
                "suspected",
                "hidden",
            }:
                raise GraphError(f"claim {claim['id']} has invalid perspective state")
        elif claim.get("perspective_id") or claim.get("perspective_state"):
            raise GraphError(
                f"objective claim {claim['id']} binds perspective metadata"
            )
        validate_value(predicate, claim.get("value"), entities)
        _require_evidence(claim, evidence_ids)
        if predicate["persistence"] == "causal":
            if claim.get("source_event_id") not in allowed_event_ids:
                raise GraphError(f"causal claim {claim['id']} has invalid source event")
            causal.append(claim)
        else:
            observations.append(claim)
    for claim in delta["perspective_changes"]:
        if claim["scope"] != "perspective":
            raise GraphError(
                f"perspective change {claim['id']} is not perspective scoped"
            )
    events = _validated_events(
        schema,
        delta["occurred_events"],
        entities,
        evidence_ids,
        allowed_event_ids,
        event_catalog,
    )
    effects = [
        {
            "op": claim["operation"],
            "subject": claim["subject_id"],
            "predicate_id": claim["predicate_id"],
            "value": claim["value"],
            "scope": claim["scope"],
            "perspective_id": claim.get("perspective_id"),
            "perspective_state": claim.get("perspective_state"),
            "valid_from": claim.get("valid_from"),
            "valid_until": claim.get("valid_until"),
            "evidence_ids": claim["evidence_ids"],
            "source_event_id": claim.get("source_event_id"),
        }
        for claim in causal
    ]
    current = {**graph, "evidence": [*graph.get("evidence", []), *delta["evidence"]]}
    indexed_effects = list(enumerate(effects))
    if anchor_order:
        indexed_effects.sort(
            key=lambda item: (
                anchor_order.get(str(item[1].get("source_event_id")), 10**9),
                item[0],
            )
        )
    for _, effect in indexed_effects:
        source_event_id = effect.pop("source_event_id")
        current = apply_effects(
            schema,
            current,
            [effect],
            {},
            event_id=source_event_id,
            anchor_order=anchor_order,
        )
    occurred = list(current.get("occurred_event_ids") or [])
    occurred.extend(item["id"] for item in events)
    if len(occurred) != len(set(occurred)):
        raise GraphError("claim delta repeats an occurred event")
    current["occurred_event_ids"] = occurred
    current = freeze_fact_graph(schema, current)
    validate_graph_constraints(
        schema,
        current,
        anchor=current_anchor,
        anchor_order=anchor_order,
    )
    patch = {
        "schema": "story_novel_state_patch.v1",
        "causal_claims": causal,
        "observations": observations,
        "occurred_events": events,
        "evidence_ids": sorted(evidence_ids),
        "snapshot_after_hash": current["snapshot_hash"],
    }
    patch["patch_hash"] = value_hash(patch)
    return {"status": "passed", "state_patch": patch, "graph_after": current}


def _validated_events(
    schema,
    rows,
    entities,
    evidence_ids,
    allowed_event_ids,
    event_catalog,
):
    types = {item["id"]: item for item in schema.get("event_types") or []}
    result = []
    for event in rows:
        if event["id"] not in allowed_event_ids or event["id"] not in event_catalog:
            raise GraphError(f"event {event['id']} is not allowed in this chapter")
        event_type = types.get(event["event_type_id"])
        if (
            not event_type
            or event_catalog[event["id"]]["event_type_id"] != event["event_type_id"]
        ):
            raise GraphError(f"event {event['id']} has invalid type")
        if set(event["role_bindings"]) != set(event_type.get("roles") or {}):
            raise GraphError(f"event {event['id']} has incomplete roles")
        for role, entity_ids in event["role_bindings"].items():
            allowed_types = set(event_type["roles"][role])
            if not entity_ids or any(
                value not in entities or entities[value]["type_id"] not in allowed_types
                for value in entity_ids
            ):
                raise GraphError(f"event {event['id']} role {role} is invalid")
        _require_evidence(event, evidence_ids)
        result.append(event)
    return result


def _require_evidence(row, evidence_ids) -> None:
    refs = row.get("evidence_ids") or []
    if not refs or not set(refs).issubset(evidence_ids):
        raise GraphError(f"{row.get('id')} has missing evidence")
