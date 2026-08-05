import json

import pytest
from app.services.story.story_novel_plan_parser import parse_plan
from app.services.story.story_novel_plan_patch_repair import (
    apply_plan_patch_response,
    plan_repair_request,
)
from tests.unit.test_story_novel_longform import _canon, _plan_row


def test_parseable_plan_uses_targeted_patch_instead_of_full_batch_rewrite():
    original = json.dumps({"chapters": [_plan_row(1)]}, ensure_ascii=False)

    prompt, patch_mode = plan_repair_request(
        "original prompt",
        original,
        "第 1 章前置状态不连续",
        [1],
        canon=_canon(),
        frozen_spec={"chapters": [_plan_row(1)]},
        thread_payoffs=[],
        prior_chapters=[],
    )

    assert patch_mode is True
    assert "不得重输整个批次" in prompt
    assert '"error_vector":"第 1 章前置状态不连续"' in prompt
    assert '"current_batch":[{"canon_refs"' in prompt


def test_unparseable_plan_falls_back_to_one_full_format_repair():
    prompt, patch_mode = plan_repair_request(
        "original prompt",
        '{"chapters":[',
        "invalid JSON",
        [1],
        canon=_canon(),
        frozen_spec={"chapters": [_plan_row(1)]},
        thread_payoffs=[],
        prior_chapters=[],
    )

    assert patch_mode is False
    assert "完整重输一次" in prompt


def test_patch_replaces_only_authorized_state_fields():
    row = _plan_row(1)
    original = json.dumps({"chapters": [row]}, ensure_ascii=False)
    patch = {
        "patches": [
            {
                "position": 1,
                "replace": {
                    "preconditions": [],
                    "location_transitions": [],
                },
            }
        ],
        "missing_chapters": [],
    }

    result = json.loads(
        apply_plan_patch_response(
            original,
            json.dumps(patch, ensure_ascii=False),
            [1],
            canon=_canon(),
            thread_payoffs=[],
        )
    )

    assert result["chapters"][0]["title"] == row["title"]
    assert result["chapters"][0]["preconditions"] == []
    assert result["chapters"][0]["location_transitions"] == []


def test_patch_result_reapplies_known_non_character_memory_normalization():
    canon = _canon()
    canon["entities"].append(
        {"id": "org-villagers", "kind": "organization", "name": "村民组织"}
    )
    original = json.dumps({"chapters": [_plan_row(1)]}, ensure_ascii=False)
    patch = {
        "patches": [
            {
                "position": 1,
                "replace": {
                    "knowledge_grants": [
                        {
                            "character_id": "org-villagers",
                            "fact_id": "fact-event-1-1",
                            "source_event_id": "event-1",
                        }
                    ]
                },
            }
        ],
        "missing_chapters": [],
    }

    result = json.loads(
        apply_plan_patch_response(
            original,
            json.dumps(patch, ensure_ascii=False),
            [1],
            canon=canon,
            thread_payoffs=[],
        )
    )

    assert result["chapters"][0]["knowledge_grants"] == []


def test_patch_routes_known_location_state_edge_to_typed_movement():
    canon = _canon()
    canon["entities"].append(
        {"id": "loc-office", "kind": "location", "name": "合作社办公处"}
    )
    original = json.dumps({"chapters": [_plan_row(1)]}, ensure_ascii=False)
    patch = {
        "patches": [
            {
                "position": 1,
                "replace": {
                    "state_transitions": [
                        {
                            "subject_id": "char-a",
                            "field": "location",
                            "from_value": "loc-gate",
                            "to_value": "loc-office",
                            "reason": "步行前往合作社办公处",
                        }
                    ]
                },
            }
        ]
    }

    result = json.loads(
        apply_plan_patch_response(
            original,
            json.dumps(patch, ensure_ascii=False),
            [1],
            canon=canon,
            thread_payoffs=[],
        )
    )

    assert result["chapters"][0]["state_transitions"] == []
    assert result["chapters"][0]["location_transitions"] == [
        {
            "subject_id": "char-a",
            "from_location_id": "loc-gate",
            "to_location_id": "loc-office",
            "means": "步行前往合作社办公处",
        }
    ]


def test_patch_rejects_narrative_contract_rewrite():
    original = json.dumps({"chapters": [_plan_row(1)]}, ensure_ascii=False)
    patch = {"patches": [{"position": 1, "replace": {"key_events": ["改写权威事件"]}}]}

    with pytest.raises(ValueError, match="越权字段"):
        apply_plan_patch_response(
            original,
            json.dumps(patch, ensure_ascii=False),
            [1],
            canon=_canon(),
            thread_payoffs=[],
        )


def test_patch_can_append_only_actually_missing_chapters():
    first = _plan_row(1)
    second = _plan_row(2)
    result = json.loads(
        apply_plan_patch_response(
            json.dumps({"chapters": [first]}, ensure_ascii=False),
            json.dumps(
                {"patches": [], "missing_chapters": [second]}, ensure_ascii=False
            ),
            [1, 2],
            canon=_canon(),
            thread_payoffs=[],
        )
    )

    assert [item["position"] for item in result["chapters"]] == [1, 2]


def test_schema_error_vector_reports_all_invalid_fields_in_one_attempt():
    first, second = _plan_row(1), _plan_row(2)
    first["target_chars"] = "not-an-integer"
    second["location_transitions"] = [
        {
            "subject_id": "char-a",
            "from_location_id": "loc-gate",
            "means": "步行",
        }
    ]

    parsed, error = parse_plan(
        json.dumps({"chapters": [first, second]}, ensure_ascii=False),
        [1, 2],
        _canon(),
        None,
    )

    assert parsed is None
    diagnostic = json.loads(error)
    assert diagnostic["kind"] == "schema"
    assert {item["path"] for item in diagnostic["issues"]} == {
        "chapters.0.target_chars",
        "chapters.1.location_transitions.0.to_location_id",
    }
    assert [item["chapter_position"] for item in diagnostic["issues"]] == [1, 2]


def test_schema_error_reports_business_position_after_prior_batches():
    prior = [_plan_row(position) for position in range(1, 45)]
    batch = [_plan_row(position) for position in range(45, 49)]
    batch[2]["state_transitions"] = [
        {
            "subject_id": "char-a",
            "field": "permissions",
            "from_value": [],
            "reason": "第 47 章取得权限",
        }
    ]

    parsed, error = parse_plan(
        json.dumps({"chapters": batch}, ensure_ascii=False),
        [45, 46, 47, 48],
        _canon(),
        None,
        prior_chapters=prior,
        require_complete=False,
    )

    assert parsed is None
    diagnostic = json.loads(error)
    assert diagnostic["issues"][0] == {
        "path": "chapters.46.state_transitions.0.to_value",
        "chapter_position": 47,
        "code": "missing",
        "message": "Field required",
    }
