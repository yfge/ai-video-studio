"""Ownership effects must not duplicate derived character inventory state."""

import pytest
from app.services.story.story_novel_canon_service import validate_generation_plan
from app.services.story.story_novel_plan_state_compiler import compile_plan_state
from tests.unit.test_story_novel_longform import _canon, _plan_row


def _owner_canon():
    canon = _canon()
    canon["entities"].extend(
        [
            {
                "id": "char-b",
                "kind": "character",
                "name": "乙",
                "aliases": [],
                "attributes": {},
            },
            {
                "id": "obj-contract",
                "kind": "object",
                "name": "试种契",
                "aliases": [],
                "attributes": {},
            },
        ]
    )
    canon["initial_state"]["char-b"] = {"possessions": []}
    canon["initial_state"]["obj-contract"] = {"owner_id": "char-a"}
    return canon


def test_compiler_drops_only_inventory_edges_mirrored_by_object_owner_transfer():
    canon = _owner_canon()
    row = _plan_row(1)
    row["state_transitions"] = [
        {
            "subject_id": "obj-contract",
            "field": "owner_id",
            "to_value": "char-b",
            "reason": "交接试种契",
        },
        {
            "subject_id": "char-a",
            "field": "possessions",
            "operation": "remove",
            "to_value": "obj-contract",
        },
        {
            "subject_id": "char-b",
            "field": "possessions",
            "operation": "add",
            "to_value": "obj-contract",
        },
    ]

    compiled = compile_plan_state(canon, [row])[0]

    assert [item["field"] for item in compiled["state_transitions"]] == ["owner_id"]
    assert compiled["state_transitions"][0]["from_value"] == "char-a"
    validate_generation_plan(canon, [compiled])


def test_compiler_drops_array_inventory_edge_mirrored_by_owner_transfer():
    canon = _owner_canon()
    canon["initial_state"]["char-a"]["possessions"] = ["obj-contract"]
    row = _plan_row(1)
    row["state_transitions"] = [
        {
            "subject_id": "obj-contract",
            "field": "owner_id",
            "to_value": "char-b",
            "reason": "交接试种契",
        },
        {
            "subject_id": "char-a",
            "field": "possessions",
            "from_value": ["obj-contract"],
            "to_value": [],
            "reason": "交出试种契",
        },
    ]

    compiled = compile_plan_state(canon, [row])[0]

    assert [item["field"] for item in compiled["state_transitions"]] == ["owner_id"]
    validate_generation_plan(canon, [compiled])


def test_compiler_keeps_array_inventory_edge_with_unrelated_change():
    canon = _owner_canon()
    canon["initial_state"]["char-a"]["possessions"] = ["obj-contract"]
    row = _plan_row(1)
    row["state_transitions"] = [
        {
            "subject_id": "obj-contract",
            "field": "owner_id",
            "to_value": "char-b",
            "reason": "交接试种契",
        },
        {
            "subject_id": "char-a",
            "field": "possessions",
            "from_value": ["obj-contract"],
            "to_value": ["obj-unplanned"],
            "reason": "夹带计划外物件变化",
        },
    ]

    compiled = compile_plan_state(canon, [row])[0]

    assert [item["field"] for item in compiled["state_transitions"]] == [
        "owner_id",
        "possessions",
    ]
    with pytest.raises(ValueError):
        validate_generation_plan(canon, [compiled])


def test_compiler_keeps_unmatched_inventory_edge_for_strict_gate_rejection():
    canon = _owner_canon()
    row = _plan_row(1)
    row["state_transitions"] = [
        {
            "subject_id": "char-a",
            "field": "possessions",
            "operation": "add",
            "to_value": "obj-contract",
        }
    ]

    compiled = compile_plan_state(canon, [row])[0]

    assert compiled["state_transitions"][0]["field"] == "possessions"
    with pytest.raises(ValueError):
        validate_generation_plan(canon, [compiled])
