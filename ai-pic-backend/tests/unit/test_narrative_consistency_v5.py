import pytest

from app.services.narrative_consistency import (
    freeze_fact_graph,
    freeze_schema,
    simulate_causal_graph,
    validate_claim_delta,
)
from app.services.narrative_consistency.errors import GraphError, SchemaError


@pytest.mark.parametrize(
    ("predicate_id", "event_type_id"),
    [
        ("suspects", "discovers"),
        ("orbits", "transfers"),
        ("trusts", "reconciles"),
        ("guards", "awakens"),
    ],
)
def test_same_engine_executes_unrelated_dynamic_vocabularies(
    predicate_id, event_type_id
):
    schema = _schema(predicate_id, event_type_id)
    initial = _graph(schema, predicate_id)
    causal = _causal(event_type_id, predicate_id)

    result = simulate_causal_graph(schema, initial, causal)

    assert result["status"] == "passed"
    facts = result["final_graph"]["facts"]
    assert [(item["predicate_id"], item["value"]) for item in facts] == [
        (predicate_id, "entity-c")
    ]


def test_observational_predicate_cannot_be_a_dependency():
    raw = _schema("links", "changes")
    raw["predicates"].append(
        {
            "id": "surface_detail",
            "label": "surface detail",
            "subject_type_ids": ["actor"],
            "value_kind": "string",
            "persistence": "observational",
        }
    )
    raw["event_types"][0]["preconditions"] = [
        {
            "op": "exists",
            "subject": {"role": "actor"},
            "predicate_id": "surface_detail",
        }
    ]

    with pytest.raises(SchemaError, match="cannot be a dependency"):
        freeze_schema(raw)


def test_cycle_and_future_dependency_fail_closed():
    schema = _schema("links", "changes")
    causal = _causal("changes", "links")
    second = {
        **causal["events"][0],
        "id": "event-2",
        "chapter_position": 2,
        "dependency_event_ids": ["event-1"],
    }
    causal["events"].append(second)
    causal["events"][0]["dependency_event_ids"] = ["event-2"]

    with pytest.raises(GraphError, match="future chapter|cycle"):
        simulate_causal_graph(schema, _graph(schema, "links"), causal)


def test_perspective_claim_requires_matching_objective_evidence():
    schema = _schema("links", "changes")
    graph = _graph(schema, "links")
    delta = _claim_delta("links", "changes", perspective=True)

    result = validate_claim_delta(
        schema,
        graph,
        delta,
        _sentences(),
        allowed_event_ids={"event-1"},
        event_catalog={"event-1": {"event_type_id": "changes"}},
    )

    perspective = result["graph_after"]["facts"][-1]
    assert perspective["scope"] == "perspective"
    assert perspective["perspective_id"] == "view-a"
    assert perspective["perspective_state"] == "believed"


def test_claim_evidence_must_be_contiguous_and_source_bound():
    schema = _schema("links", "changes")
    graph = _graph(schema, "links")
    delta = _claim_delta("links", "changes")
    delta["evidence"][0]["sentence_ids"] = ["S0001", "S0003"]

    with pytest.raises(GraphError, match="not contiguous"):
        validate_claim_delta(
            schema,
            graph,
            delta,
            _sentences(),
            allowed_event_ids={"event-1"},
            event_catalog={"event-1": {"event_type_id": "changes"}},
        )


def test_observation_is_retained_outside_causal_snapshot():
    raw = _schema("links", "changes")
    raw["predicates"].append(
        {
            "id": "tone",
            "label": "tone",
            "subject_type_ids": ["actor"],
            "value_kind": "string",
            "persistence": "observational",
        }
    )
    schema = freeze_schema(raw)
    delta = _claim_delta("tone", "changes")
    delta["claims"][0]["operation"] = "assert"
    delta["claims"][0]["value"] = "quiet"

    result = validate_claim_delta(
        schema,
        _graph(schema, "links"),
        delta,
        _sentences(),
        allowed_event_ids={"event-1"},
        event_catalog={"event-1": {"event_type_id": "changes"}},
    )

    assert result["state_patch"]["causal_claims"] == []
    assert result["state_patch"]["observations"][0]["predicate_id"] == "tone"


def test_unknown_perspective_in_effect_fails_schema_freeze():
    raw = _schema("links", "changes")
    raw.pop("schema_hash", None)
    raw["event_types"][0]["effects"] = [
        {
            "op": "reveal",
            "subject": {"role": "actor"},
            "predicate_id": "links",
            "value": {"role": "target"},
            "perspective_id": "unknown-view",
        }
    ]

    with pytest.raises(SchemaError, match="unknown perspective"):
        freeze_schema(raw)


def test_unknown_predicate_in_event_effect_fails_schema_freeze():
    raw = _schema("links", "changes")
    raw.pop("schema_hash", None)
    raw["event_types"][0]["effects"] = [
        {
            "op": "assert",
            "subject": {"role": "actor"},
            "predicate_id": "not-in-this-story",
            "value": {"role": "target"},
        }
    ]

    with pytest.raises(SchemaError, match="unknown predicate"):
        freeze_schema(raw)


def _schema(predicate_id, event_type_id):
    return freeze_schema(
        {
            "schema": "story_novel_consistency_schema.v1",
            "version": 1,
            "entity_types": [
                {"id": "actor", "label": "actor", "capabilities": ["perspective"]},
                {"id": "subject", "label": "subject", "capabilities": []},
            ],
            "predicates": [
                {
                    "id": predicate_id,
                    "label": predicate_id,
                    "subject_type_ids": ["actor"],
                    "value_kind": "entity_ref",
                    "value_entity_type_ids": ["subject"],
                    "cardinality": "one",
                    "mutability": "replaceable",
                    "persistence": "causal",
                }
            ],
            "event_types": [
                {
                    "id": event_type_id,
                    "label": event_type_id,
                    "roles": {"actor": ["actor"], "target": ["subject"]},
                }
            ],
            "constraints": [],
            "perspectives": [
                {"id": "view-a", "kind": "holder", "holder_entity_id": "entity-a"}
            ],
            "source_manifest": {"story_seed_version": 1},
        }
    )


def _graph(schema, predicate_id):
    return freeze_fact_graph(
        schema,
        {
            "schema": "story_novel_fact_graph.v1",
            "entities": [
                {"id": "entity-a", "type_id": "actor", "name": "A"},
                {"id": "entity-b", "type_id": "subject", "name": "B"},
                {"id": "entity-c", "type_id": "subject", "name": "C"},
            ],
            "facts": [
                {
                    "id": "fact-initial",
                    "subject_id": "entity-a",
                    "predicate_id": predicate_id,
                    "value": "entity-b",
                }
            ],
            "evidence": [],
            "occurred_event_ids": [],
        },
    )


def _causal(event_type_id, predicate_id):
    return {
        "schema": "story_novel_causal_event_graph.v1",
        "events": [
            {
                "id": "event-1",
                "event_type_id": event_type_id,
                "chapter_position": 1,
                "role_bindings": {"actor": ["entity-a"], "target": ["entity-c"]},
                "effects": [
                    {
                        "op": "replace",
                        "subject": {"role": "actor"},
                        "predicate_id": predicate_id,
                        "value": {"role": "target"},
                    }
                ],
            }
        ],
        "obligations": [],
    }


def _claim_delta(predicate_id, event_type_id, perspective=False):
    claim = {
        "id": "claim-1",
        "operation": "replace" if not perspective else "assert",
        "subject_id": "entity-a",
        "predicate_id": predicate_id,
        "value": "entity-c" if not perspective else "entity-b",
        "scope": "perspective" if perspective else "objective",
        "perspective_id": "view-a" if perspective else None,
        "perspective_state": "believed" if perspective else None,
        "source_event_id": "event-1",
        "evidence_ids": ["evidence-1"],
    }
    return {
        "schema": "story_novel_claim_delta.v1",
        "claims": [] if perspective else [claim],
        "perspective_changes": [claim] if perspective else [],
        "occurred_events": [
            {
                "id": "event-1",
                "event_type_id": event_type_id,
                "role_bindings": {"actor": ["entity-a"], "target": ["entity-c"]},
                "evidence_ids": ["evidence-1"],
            }
        ],
        "evidence": [
            {
                "id": "evidence-1",
                "source_artifact_type": "novel_chapter",
                "source_artifact_id": "chapter-1",
                "source_version": 1,
                "source_hash": "body-hash",
                "sentence_ids": ["S0001"],
                "quote": "A走向C。",
            }
        ],
    }


def _sentences():
    return [
        {"sentence_id": "S0001", "text": "A走向C。"},
        {"sentence_id": "S0002", "text": "风停了。"},
        {"sentence_id": "S0003", "text": "门关上。"},
    ]
