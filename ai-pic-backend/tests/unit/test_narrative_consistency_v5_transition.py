import copy

import pytest

from app.services.narrative_consistency import (
    freeze_fact_graph,
    freeze_schema,
    simulate_causal_graph,
    validate_chapter_transition,
    validate_claim_delta,
)
from app.services.narrative_consistency.errors import GraphError
from tests.unit.test_narrative_consistency_v5 import (
    _causal,
    _claim_delta,
    _graph,
    _schema,
    _sentences,
)


def test_runtime_transition_requires_exact_planned_effects_and_events():
    schema = _schema("links", "changes")
    graph = _graph(schema, "links")
    causal = _causal("changes", "links")
    catalog = {"event-1": causal["events"][0]}

    result = validate_chapter_transition(
        schema,
        graph,
        _claim_delta("links", "changes"),
        _sentences(),
        allowed_event_ids={"event-1"},
        event_catalog=catalog,
    )

    assert result["graph_after"]["facts"][0]["value"] == "entity-c"
    assert result["state_patch"]["occurred_events"][0]["id"] == "event-1"

    missing = _claim_delta("links", "changes")
    missing["occurred_events"] = []
    with pytest.raises(GraphError, match="chapter events mismatch"):
        validate_chapter_transition(
            schema,
            graph,
            missing,
            _sentences(),
            allowed_event_ids={"event-1"},
            event_catalog=catalog,
        )

    contradicted = _claim_delta("links", "changes")
    contradicted["claims"][0]["value"] = "entity-b"
    with pytest.raises(GraphError, match="do not match planned event effects"):
        validate_chapter_transition(
            schema,
            graph,
            contradicted,
            _sentences(),
            allowed_event_ids={"event-1"},
            event_catalog=catalog,
        )


def test_temporal_fact_is_inactive_at_its_exclusive_end_anchor():
    raw = copy.deepcopy(_schema("links", "changes"))
    raw.pop("schema_hash", None)
    raw["predicates"][0]["temporal"] = True
    raw["event_types"][0]["preconditions"] = [
        {
            "op": "exists",
            "subject": {"role": "actor"},
            "predicate_id": "links",
        }
    ]
    schema = freeze_schema(raw)
    graph = copy.deepcopy(_graph(schema, "links"))
    graph.pop("snapshot_hash", None)
    graph["facts"][0]["valid_until"] = "event-1"
    graph = freeze_fact_graph(schema, graph)

    with pytest.raises(GraphError, match="preconditions are not satisfied"):
        simulate_causal_graph(schema, graph, _causal("changes", "links"))


def test_unknown_temporal_anchor_fails_closed():
    raw = copy.deepcopy(_schema("links", "changes"))
    raw.pop("schema_hash", None)
    raw["predicates"][0]["temporal"] = True
    schema = freeze_schema(raw)
    graph = copy.deepcopy(_graph(schema, "links"))
    graph.pop("snapshot_hash", None)
    graph["facts"][0]["valid_from"] = "event-never"
    graph = freeze_fact_graph(schema, graph)

    with pytest.raises(GraphError, match="unknown valid_from"):
        simulate_causal_graph(schema, graph, _causal("changes", "links"))


def test_claim_application_rechecks_blocking_unique_constraint():
    raw = copy.deepcopy(_schema("links", "changes"))
    raw.pop("schema_hash", None)
    raw["constraints"] = [
        {
            "id": "unique-links",
            "kind": "unique",
            "severity": "blocking",
            "expression": {"predicate_id": "links"},
        }
    ]
    schema = freeze_schema(raw)
    graph = copy.deepcopy(_graph(schema, "links"))
    graph.pop("snapshot_hash", None)
    graph["entities"].append({"id": "entity-d", "type_id": "actor", "name": "D"})
    graph = freeze_fact_graph(schema, graph)
    delta = _claim_delta("links", "changes")
    delta["claims"][0].update(
        operation="assert", subject_id="entity-d", value="entity-b"
    )

    with pytest.raises(GraphError, match="unique constraint failed"):
        validate_claim_delta(
            schema,
            graph,
            delta,
            _sentences(),
            allowed_event_ids={"event-1"},
            event_catalog={"event-1": {"event_type_id": "changes"}},
        )


def test_temporal_replacements_keep_history_but_only_one_active_value():
    raw = copy.deepcopy(_schema("links", "changes"))
    raw.pop("schema_hash", None)
    raw["predicates"][0]["temporal"] = True
    schema = freeze_schema(raw)
    causal = _causal("changes", "links")
    second = copy.deepcopy(causal["events"][0])
    second.update(
        id="event-2",
        chapter_position=2,
        dependency_event_ids=["event-1"],
        role_bindings={"actor": ["entity-a"], "target": ["entity-b"]},
    )
    causal["events"].append(second)

    result = simulate_causal_graph(schema, _graph(schema, "links"), causal)
    facts = result["final_graph"]["facts"]

    assert [item.get("valid_until") for item in facts[:-1]] == [
        "event-1",
        "event-2",
    ]
    assert facts[-1]["value"] == "entity-b"
    assert facts[-1]["valid_from"] == "event-2"


def test_same_chapter_order_constraint_requires_a_dependency_path():
    raw = copy.deepcopy(_schema("links", "changes"))
    raw.pop("schema_hash", None)
    raw["constraints"] = [
        {
            "id": "ordered-events",
            "kind": "order",
            "severity": "blocking",
            "expression": {
                "before_event_id": "event-1",
                "after_event_id": "event-2",
            },
        }
    ]
    schema = freeze_schema(raw)
    causal = _causal("changes", "links")
    second = copy.deepcopy(causal["events"][0])
    second.update(id="event-2", dependency_event_ids=[])
    causal["events"].append(second)

    with pytest.raises(GraphError, match="order constraint failed"):
        simulate_causal_graph(schema, _graph(schema, "links"), causal)

    causal["events"][1]["dependency_event_ids"] = ["event-1"]
    assert (
        simulate_causal_graph(schema, _graph(schema, "links"), causal)["status"]
        == "passed"
    )


def test_mutually_exclusive_initial_facts_fail_before_generation():
    raw = copy.deepcopy(_schema("links", "changes"))
    raw.pop("schema_hash", None)
    raw["predicates"].append(
        {
            "id": "sealed",
            "label": "sealed",
            "subject_type_ids": ["actor"],
            "value_kind": "boolean",
            "persistence": "causal",
        }
    )
    raw["constraints"] = [
        {
            "id": "exclusive-state",
            "kind": "mutual_exclusion",
            "severity": "blocking",
            "expression": {
                "conditions": [
                    {
                        "op": "equals",
                        "subject": "entity-a",
                        "predicate_id": "links",
                        "value": "entity-b",
                    },
                    {
                        "op": "equals",
                        "subject": "entity-a",
                        "predicate_id": "sealed",
                        "value": True,
                    },
                ]
            },
        }
    ]
    schema = freeze_schema(raw)
    graph = copy.deepcopy(_graph(schema, "links"))
    graph.pop("snapshot_hash", None)
    graph["facts"].append(
        {
            "id": "fact-sealed",
            "subject_id": "entity-a",
            "predicate_id": "sealed",
            "value": True,
        }
    )

    with pytest.raises(GraphError, match="mutual exclusion failed"):
        simulate_causal_graph(schema, graph, _causal("changes", "links"))


def test_reveal_cannot_leak_an_absent_objective_fact():
    raw = copy.deepcopy(_schema("links", "changes"))
    raw.pop("schema_hash", None)
    raw["event_types"][0]["effects"] = [
        {
            "op": "reveal",
            "subject": {"role": "actor"},
            "predicate_id": "links",
            "value": {"role": "target"},
            "perspective_id": "view-a",
        }
    ]
    schema = freeze_schema(raw)

    with pytest.raises(GraphError, match="cannot reveal absent objective fact"):
        simulate_causal_graph(
            schema,
            _graph(schema, "links"),
            _causal("changes", "links"),
        )
