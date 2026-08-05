import copy

import pytest
from app.services.story.story_novel_brief_location_scope import brief_allowed_entity_ids
from app.services.story.story_novel_chapter_brief_contract import (
    compile_chapter_brief_input,
    validate_chapter_brief,
    validate_model_brief,
)
from tests.unit.test_story_novel_v3_brief_contract import _brief, _chapter


def _input_with_locations():
    chapter = _chapter()
    chapter["location_transitions"] = [
        {
            "subject_id": "char-su-yan",
            "from_location_id": "loc-canal",
            "to_location_id": "loc-field",
            "means": "步行",
        }
    ]
    planning_input = compile_chapter_brief_input(
        chapter,
        {"subjects": {"char-su-yan": {"location": "loc-canal"}}},
        allowed_entity_ids=[
            "char-su-yan",
            "sample-r17",
            "loc-village",
            "loc-canal",
            "loc-field",
            "loc-house",
        ],
    )
    planning_input["hard_constraints"] = {
        "compiled_canon": {
            "entities": [
                {"id": "char-su-yan", "kind": "character", "name": "苏砚"},
                {
                    "id": "loc-village",
                    "kind": "location",
                    "attributes": {},
                },
                {
                    "id": "loc-canal",
                    "kind": "location",
                    "attributes": {"parent_location_id": "loc-village"},
                },
                {
                    "id": "loc-field",
                    "kind": "location",
                    "attributes": {"parent_location_id": "loc-village"},
                },
                {
                    "id": "loc-house",
                    "kind": "location",
                    "attributes": {"parent_location_id": "loc-village"},
                },
            ]
        }
    }
    return planning_input


def test_new_brief_rejects_location_outside_current_transition_path():
    planning_input = _input_with_locations()
    brief = _brief(planning_input)
    brief["beats"][0]["allowed_entity_ids"].append("loc-house")

    with pytest.raises(ValueError, match="loc-house"):
        validate_chapter_brief(brief, planning_input, enforce_location_scope=True)


def test_new_brief_allows_current_destination_and_parent_location():
    planning_input = _input_with_locations()
    brief = _brief(planning_input)
    brief["beats"][0]["allowed_entity_ids"].extend(
        ["loc-canal", "loc-field", "loc-village"]
    )

    validated = validate_chapter_brief(
        copy.deepcopy(brief), planning_input, enforce_location_scope=True
    )

    assert validated["brief_hash"]


def test_service_bound_allow_list_excludes_visible_but_off_path_location():
    planning_input = _input_with_locations()

    allowed = brief_allowed_entity_ids(planning_input)

    assert "char-su-yan" in allowed
    assert "sample-r17" in allowed
    assert {"loc-village", "loc-canal", "loc-field"}.issubset(allowed)
    assert "loc-house" not in allowed


def test_model_brief_drops_invented_scene_prop_ids():
    planning_input = _input_with_locations()
    brief = _brief(planning_input)
    brief["beats"][0]["allowed_entity_ids"].append("obj-seed-bag-1")
    brief["beats"][0]["purpose"] = "把两袋谷种分开封样，不创建状态实体"

    validated = validate_model_brief(brief, planning_input)

    assert "obj-seed-bag-1" not in validated["beats"][0]["allowed_entity_ids"]
    assert "两袋谷种" in validated["beats"][0]["purpose"]
