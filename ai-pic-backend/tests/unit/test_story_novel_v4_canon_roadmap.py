import json

import pytest
from app.services.story.story_novel_canon_service import parse_model_canon
from tests.unit.test_story_novel_longform import _canon


def _contract():
    return {
        "story_seed": {
            "world_constraints": [],
            "structured_outline": {
                "planning_structure_version": 1,
                "chapters": [{"position": 1, "key_events": ["启程"]}],
                "core_character_routes": [
                    {
                        "character_ref": "char-a",
                        "narrative_function": "持续成长的主角",
                        "first_allowed_position": 1,
                        "planned_arc_id": "arc-1",
                        "relationship_targets": [],
                        "start_direction": "受困",
                        "turning_directions": ["主动选择"],
                        "terminal_direction": "承担责任",
                        "hidden_state": {"permissions": ["local"]},
                    }
                ],
                "initial_scope_nodes": [
                    {
                        "scope_id": "loc-a",
                        "scope_type": "起始活动范围",
                        "display_name": "旧宅",
                        "parent_scope_id": None,
                        "depth": 0,
                        "first_allowed_position": 1,
                        "visibility": "visited",
                        "governing_entities": [],
                        "local_rules": ["夜间关闭"],
                    }
                ],
                "initial_scope_edges": [],
            },
        }
    }


def _payload():
    value = _canon()
    value["timeline"] = []
    character = next(item for item in value["entities"] if item["id"] == "char-a")
    character["attributes"] = {}
    location = next(item for item in value["entities"] if item["kind"] == "location")
    location.update(id="loc-a", name="旧宅", attributes={})
    value["initial_state"] = {
        ("loc-a" if key == "loc-a" else key): row
        for key, row in value["initial_state"].items()
    }
    for row in value["initial_state"].values():
        if row.get("location"):
            row["location"] = "loc-a"
    return value


def test_model_canon_is_bound_to_frozen_character_and_scope_roadmap():
    canon, error, _diagnostics = parse_model_canon(
        json.dumps(_payload(), ensure_ascii=False), _contract()
    )

    assert error is None
    character = next(item for item in canon["entities"] if item["id"] == "char-a")
    location = next(item for item in canon["entities"] if item["id"] == "loc-a")
    assert character["attributes"]["planned_arc_id"] == "arc-1"
    assert canon["initial_state"]["char-a"]["permissions"] == ["local"]
    assert location["attributes"]["scope_type"] == "起始活动范围"
    assert location["attributes"]["local_rules"] == ["夜间关闭"]


def test_model_canon_rejects_missing_future_core_character():
    payload = _payload()
    payload["entities"] = [
        item for item in payload["entities"] if item["id"] != "char-a"
    ]
    payload["initial_state"].pop("char-a", None)

    canon, error, _diagnostics = parse_model_canon(
        json.dumps(payload, ensure_ascii=False), _contract()
    )

    assert canon is None
    assert "核心人物路线缺少 Canon character" in error
