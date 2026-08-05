from copy import deepcopy

import pytest
from app.schemas.story_novel_longform import (
    StoryNovelGenerationPlan,
    StoryNovelLocationTransition,
)
from app.services.story.story_novel_canon_service import (
    normalize_canon,
    validate_generation_plan,
)
from app.services.story.story_novel_state_service import initial_story_state
from app.services.story.story_novel_state_validator import validate_state_delta
from pydantic import ValidationError
from tests.unit.test_story_novel_longform import _canon, _plan_row


def _object_creation_case(initial_status="不存在"):
    canon_raw = _canon()
    canon_raw["entities"].append(
        {
            "id": "obj-fragment",
            "kind": "object",
            "name": "风钥残片",
            "aliases": [],
            "attributes": {},
        }
    )
    canon_raw["initial_state"]["obj-fragment"] = {"status": initial_status}
    canon = normalize_canon(canon_raw)
    chapter = _plan_row(1)
    chapter["state_transitions"] = [
        {
            "subject_id": "obj-fragment",
            "field": "status",
            "from_value": initial_status,
            "to_value": "已存档",
            "reason": "本章首次生成并归档",
        }
    ]
    chapter["location_transitions"] = [
        {
            "subject_id": "obj-fragment",
            "from_location_id": None,
            "to_location_id": "loc-gate",
            "means": "生成后由档案员收入公共档案",
        }
    ]
    return canon, chapter


def _delta(chapter):
    return {
        "occurred_event_ids": list(chapter["required_event_ids"]),
        "premature_future_event_ids": [],
        "state_transitions": list(chapter["state_transitions"]),
        "knowledge_grants": [],
        "location_transitions": list(chapter["location_transitions"]),
        "milestones_consumed": [],
        "opened_thread_ids": [],
        "resolved_thread_ids": [],
        "world_rule_violations": [],
    }


@pytest.mark.parametrize("initial_status", ["尚未存在", "not_built"])
def test_schema_and_plan_allow_same_chapter_object_creation_placement(initial_status):
    canon, chapter = _object_creation_case(initial_status)
    parsed = StoryNovelGenerationPlan.model_validate({"chapters": [chapter]})
    assert parsed.chapters[0].location_transitions[0].from_location_id is None
    validate_generation_plan(canon, parsed.model_dump()["chapters"])
    report, _ = validate_state_delta(
        canon, chapter, initial_story_state(canon), _delta(chapter)
    )
    assert report["status"] == "passed"


def test_schema_requires_explicit_nullable_origin():
    movement = {
        "subject_id": "obj-fragment",
        "to_location_id": "loc-gate",
        "means": "首次归档",
    }
    with pytest.raises(ValidationError):
        StoryNovelLocationTransition.model_validate(movement)
    movement["from_location_id"] = None
    parsed = StoryNovelLocationTransition.model_validate(movement)
    assert parsed.from_location_id is None


def test_state_gate_allows_extracted_object_creation_placement():
    canon, chapter = _object_creation_case("尚未存在")
    report, state_after = validate_state_delta(
        canon,
        chapter,
        initial_story_state(canon),
        _delta(chapter),
    )

    assert report == {"status": "passed", "violations": []}
    assert state_after["subjects"]["obj-fragment"] == {
        "status": "已存档",
        "location": "loc-gate",
    }


def test_null_origin_rejected_for_character_travel():
    canon, chapter = _object_creation_case()
    chapter["location_transitions"][0]["subject_id"] = "char-a"

    with pytest.raises(ValueError, match="地点起点不连续"):
        validate_generation_plan(canon, [chapter])


def test_null_origin_rejected_without_same_chapter_object_creation():
    canon, chapter = _object_creation_case()
    chapter["state_transitions"] = []

    with pytest.raises(ValueError, match="地点起点不连续"):
        validate_generation_plan(canon, [chapter])

    report, _state_after = validate_state_delta(
        canon,
        chapter,
        initial_story_state(canon),
        _delta(chapter),
    )
    assert report["status"] == "failed"
    assert any(item["code"] == "unexplained_location" for item in report["violations"])


def test_null_origin_rejects_missing_explicit_initial_absence():
    canon, chapter = _object_creation_case()
    raw = deepcopy(canon)
    raw.pop("canon_hash", None)
    raw["initial_state"]["obj-fragment"].pop("status")
    canon = normalize_canon(raw)
    chapter["state_transitions"][0]["from_value"] = None

    with pytest.raises(ValueError, match="地点起点不连续"):
        validate_generation_plan(canon, [chapter])

    report, _state_after = validate_state_delta(
        canon, chapter, initial_story_state(canon), _delta(chapter)
    )
    assert report["status"] == "failed"
    assert any(item["code"] == "unexplained_location" for item in report["violations"])


def test_null_origin_rejects_status_absence_wash_chain():
    canon, chapter = _object_creation_case()
    raw = deepcopy(canon)
    raw.pop("canon_hash", None)
    raw["initial_state"]["obj-fragment"]["status"] = "在库"
    canon = normalize_canon(raw)
    chapter["state_transitions"] = [
        {
            "subject_id": "obj-fragment",
            "field": "status",
            "from_value": "在库",
            "to_value": "不存在",
            "reason": "伪造缺失",
        },
        {
            "subject_id": "obj-fragment",
            "field": "status",
            "from_value": "不存在",
            "to_value": "已存档",
            "reason": "洗白为首次出现",
        },
    ]

    with pytest.raises(ValueError, match="地点起点不连续"):
        validate_generation_plan(canon, [chapter])

    report, _state_after = validate_state_delta(
        canon, chapter, initial_story_state(canon), _delta(chapter)
    )
    assert report["status"] == "failed"
    assert any(item["code"] == "unexplained_location" for item in report["violations"])


def test_state_gate_rejects_extracted_transition_from_mismatch():
    canon, chapter = _object_creation_case()
    delta = _delta(chapter)
    delta["state_transitions"][0]["from_value"] = None

    report, _state_after = validate_state_delta(
        canon, chapter, initial_story_state(canon), delta
    )

    assert report["status"] == "failed"
    assert any(item["code"] == "state_reversion" for item in report["violations"])


def test_second_null_placement_is_rejected_after_first_application():
    canon, chapter = _object_creation_case()
    first_report, state_after = validate_state_delta(
        canon, chapter, initial_story_state(canon), _delta(chapter)
    )
    assert first_report["status"] == "passed"
    second = deepcopy(chapter)
    second["position"] = 2
    second["required_event_ids"] = ["event-2"]
    second["state_transitions"][0].update(
        from_value="已存档",
        to_value="再次归档",
    )

    report, _state_after = validate_state_delta(
        canon, second, state_after, _delta(second)
    )
    assert report["status"] == "failed"
    assert any(item["code"] == "unexplained_location" for item in report["violations"])


def test_null_creation_rejects_multiple_same_chapter_movements():
    canon, chapter = _object_creation_case()
    raw = deepcopy(canon)
    raw.pop("canon_hash", None)
    raw["entities"].append(
        {
            "id": "loc-vault",
            "kind": "location",
            "name": "档案库",
            "aliases": [],
            "attributes": {},
        }
    )
    canon = normalize_canon(raw)
    chapter["location_transitions"].append(
        {
            "subject_id": "obj-fragment",
            "from_location_id": "loc-gate",
            "to_location_id": "loc-vault",
            "means": "继续转入档案库",
        }
    )

    with pytest.raises(ValueError, match="地点起点不连续"):
        validate_generation_plan(canon, [chapter])


def test_non_null_origin_must_match_current_location():
    canon, chapter = _object_creation_case()
    chapter["location_transitions"][0]["from_location_id"] = "loc-gate"

    with pytest.raises(ValueError, match="地点起点不连续"):
        validate_generation_plan(canon, [chapter])
