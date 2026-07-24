from copy import deepcopy

import pytest
from app.services.story.story_novel_canon_service import (
    normalize_canon,
    validate_generation_plan,
)
from app.services.story.story_novel_initial_state import (
    apply_subject_transition,
    canonical_initial_subjects,
)
from app.services.story.story_novel_plan_repair import (
    _repair_context,
    plan_repair_prompt,
)
from app.services.story.story_novel_planning_prompt import planning_prompt
from app.services.story.story_novel_state_service import (
    apply_state_delta,
    initial_story_state,
)
from app.services.story.story_novel_state_validator import validate_state_delta
from tests.unit.test_story_novel_longform import _canon, _plan_row
from tests.unit.test_story_novel_object_creation_location import (
    _delta,
    _object_creation_case,
)


@pytest.mark.parametrize(
    ("target_status", "reason"),
    [
        (None, "首次生成"),
        ("", "首次生成"),
        (" ", "首次生成"),
        ("destroyed", "首次生成"),
        ("已销毁", "首次生成"),
        ("已归档", " "),
    ],
)
def test_initial_null_placement_requires_present_status_and_reason(
    target_status, reason
):
    canon, chapter = _object_creation_case()
    transition = chapter["state_transitions"][0]
    transition.update(to_value=target_status, reason=reason)

    with pytest.raises(ValueError, match="地点起点不连续"):
        validate_generation_plan(canon, [chapter])
    report, _state_after = validate_state_delta(
        canon, chapter, initial_story_state(canon), _delta(chapter)
    )

    assert report["status"] == "failed"
    assert any(item["code"] == "unexplained_location" for item in report["violations"])


def test_initial_null_placement_keeps_exact_present_creation_valid():
    canon, chapter = _object_creation_case("尚未创建")
    chapter["state_transitions"][0].update(
        to_value="已归档",
        reason="本章首次生成并归档",
    )

    validate_generation_plan(canon, [chapter])
    report, state_after = validate_state_delta(
        canon, chapter, initial_story_state(canon), _delta(chapter)
    )

    assert report == {"status": "passed", "violations": []}
    assert state_after["subjects"]["obj-fragment"]["status"] == "已归档"


def test_movement_requires_nonblank_means_in_plan_and_runtime():
    canon, chapter = _object_creation_case()
    chapter["location_transitions"][0]["means"] = " "

    with pytest.raises(ValueError, match="地点移动缺少有效过程"):
        validate_generation_plan(canon, [chapter])
    report, _state_after = validate_state_delta(
        canon, chapter, initial_story_state(canon), _delta(chapter)
    )

    assert any(item["code"] == "unexplained_location" for item in report["violations"])


def test_character_inventory_is_derived_for_owner_transfer():
    raw = _canon()
    raw["entities"].extend(
        [
            {
                "id": "char-b",
                "kind": "character",
                "name": "接收者",
                "aliases": [],
                "attributes": {"location": "loc-vault"},
            },
            {
                "id": "obj-key",
                "kind": "object",
                "name": "钥匙",
                "aliases": [],
                "attributes": {},
            },
            {
                "id": "loc-vault",
                "kind": "location",
                "name": "档案库",
                "aliases": [],
                "attributes": {},
            },
        ]
    )
    raw["initial_state"]["obj-key"] = {
        "owner_id": "char-a",
        "location": "loc-gate",
    }
    subjects = canonical_initial_subjects(normalize_canon(raw))

    assert subjects["char-a"]["possessions"] == ["obj-key"]
    assert subjects["char-b"]["possessions"] == []
    apply_subject_transition(subjects, "obj-key", "owner_id", "char-b")

    assert subjects["char-a"]["possessions"] == []
    assert subjects["char-b"]["possessions"] == ["obj-key"]
    assert subjects["obj-key"] == {
        "owner_id": "char-b",
        "location": "loc-vault",
    }


@pytest.mark.parametrize(
    ("field", "from_value", "to_value"),
    [
        ("knowledge", [], ["fact-1"]),
        ("location", "loc-gate", "loc-other"),
        ("possessions", [], ["obj-key"]),
    ],
    ids=["knowledge", "location", "inventory"],
)
def test_direct_derived_state_transitions_fail_plan_and_runtime(
    field, from_value, to_value
):
    canon = normalize_canon(_canon())
    chapter = _plan_row(1)
    chapter["state_transitions"] = [
        {
            "subject_id": "char-a",
            "field": field,
            "from_value": from_value,
            "to_value": to_value,
            "reason": "绕过专用 typed delta",
        }
    ]

    with pytest.raises(ValueError, match="不能写入 state_transitions"):
        validate_generation_plan(canon, [chapter])
    report, _state_after = validate_state_delta(
        canon, chapter, initial_story_state(canon), _delta(chapter)
    )

    assert any(
        item["code"] == "canon_violation"
        and "不能写入 state_transitions" in item["message"]
        for item in report["violations"]
    )


def test_noop_location_transition_fails_plan_and_runtime():
    canon = normalize_canon(_canon())
    chapter = _plan_row(1)
    chapter["location_transitions"] = [
        {
            "subject_id": "char-a",
            "from_location_id": "loc-gate",
            "to_location_id": "loc-gate",
            "means": "伪造原地移动",
        }
    ]

    with pytest.raises(ValueError, match="地点移动起终点相同"):
        validate_generation_plan(canon, [chapter])
    report, _state_after = validate_state_delta(
        canon, chapter, initial_story_state(canon), _delta(chapter)
    )

    assert any(item["code"] == "unexplained_location" for item in report["violations"])


def test_unpositioned_once_only_milestone_is_not_executable_or_repairable():
    raw = _canon()
    raw["milestones"] = [
        {
            "id": "mile-unpositioned",
            "label": "尚未排期的选择",
            "planned_position": None,
            "repeatable": False,
            "outcomes": [],
        }
    ]
    canon = normalize_canon(raw)
    chapter = _plan_row(1)
    chapter["milestones_consumed"] = ["mile-unpositioned"]
    delta = _delta(chapter)
    delta["milestones_consumed"] = ["mile-unpositioned"]

    with pytest.raises(ValueError, match="未指定章节的不可逆里程碑不能消费"):
        validate_generation_plan(canon, [chapter])
    report, _state_after = validate_state_delta(
        canon, chapter, initial_story_state(canon), delta
    )
    assert any(
        "未指定章节的不可逆里程碑不能消费" in item["message"]
        for item in report["violations"]
    )

    context = _repair_context(
        '{"chapters":[{"position":1,"milestones_consumed":["mile-unpositioned"]}]}',
        "mile-unpositioned",
        canon,
        {"chapters": []},
        None,
    )
    assert "mile-unpositioned" not in str(context)
    assert "planned_position 为 null 的不可逆 milestone" in planning_prompt(
        planning_contract={}, canon=canon
    )
    assert "planned_position 为 null 的不可逆 milestone" in plan_repair_prompt(
        "原始提示",
        '{"chapters":[]}',
        None,
        [],
        canon=canon,
        frozen_spec={"chapters": []},
    )


def test_knowledge_grant_requires_a_current_chapter_source_event():
    canon = normalize_canon(_canon())
    first = _plan_row(1)
    second = _plan_row(2)
    second["knowledge_grants"] = [
        {
            "character_id": "char-a",
            "fact_id": "fact-retold",
            "source_event_id": "event-1",
        }
    ]

    with pytest.raises(ValueError, match="知识来源不是本章事件"):
        validate_generation_plan(canon, [first, second])
    state_before = apply_state_delta(
        initial_story_state(canon), {"occurred_event_ids": ["event-1"]}
    )
    report, _state_after = validate_state_delta(
        canon,
        second,
        state_before,
        {**_delta(second), "knowledge_grants": second["knowledge_grants"]},
    )
    assert any(item["code"] == "illegal_knowledge" for item in report["violations"])

    second = deepcopy(second)
    second["knowledge_grants"][0]["source_event_id"] = "event-2"
    validate_generation_plan(canon, [first, second])
    report, _state_after = validate_state_delta(
        canon,
        second,
        state_before,
        {**_delta(second), "knowledge_grants": second["knowledge_grants"]},
    )
    assert report == {"status": "passed", "violations": []}
