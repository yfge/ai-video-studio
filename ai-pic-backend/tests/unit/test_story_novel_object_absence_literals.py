from copy import deepcopy

import pytest
from app.services.story.story_novel_canon_service import (
    normalize_canon,
    validate_generation_plan,
)
from app.services.story.story_novel_location_rules import ABSENT_OBJECT_STATUS_LITERALS
from app.services.story.story_novel_state_service import initial_story_state
from app.services.story.story_novel_state_validator import validate_state_delta
from tests.unit.test_story_novel_object_creation_location import (
    _delta,
    _object_creation_case,
)


@pytest.mark.parametrize("status", ABSENT_OBJECT_STATUS_LITERALS)
def test_exact_absence_literals_allow_initial_object_placement(status):
    canon, chapter = _object_creation_case(status)

    validate_generation_plan(canon, [chapter])
    report, state_after = validate_state_delta(
        canon, chapter, initial_story_state(canon), _delta(chapter)
    )

    assert report == {"status": "passed", "violations": []}
    assert state_after["subjects"]["obj-fragment"]["location"] == "loc-gate"


@pytest.mark.parametrize(
    "status",
    [
        "未发现",
        "未找到",
        "未签发",
        "未采集",
        "ABSENT",
        " not-created ",
        "not_created",
    ],
)
def test_other_statuses_reject_null_origin_in_plan_and_runtime(status):
    canon, chapter = _object_creation_case(status)

    with pytest.raises(ValueError, match="地点起点不连续"):
        validate_generation_plan(canon, [chapter])
    report, _state_after = validate_state_delta(
        canon, chapter, initial_story_state(canon), _delta(chapter)
    )

    assert report["status"] == "failed"
    assert any(item["code"] == "unexplained_location" for item in report["violations"])


def test_defined_empty_array_is_not_an_undefined_from_value():
    canon, chapter = _object_creation_case()
    raw = deepcopy(canon)
    raw.pop("canon_hash", None)
    raw["initial_state"]["obj-fragment"]["permissions"] = []
    canon = normalize_canon(raw)
    chapter["location_transitions"] = []
    chapter["state_transitions"] = [
        {
            "subject_id": "obj-fragment",
            "field": "permissions",
            "from_value": None,
            "to_value": ["三级权限"],
            "reason": "获得权限",
        }
    ]

    with pytest.raises(ValueError, match="状态起点不连续"):
        validate_generation_plan(canon, [chapter])
    bad_report, _state_after = validate_state_delta(
        canon, chapter, initial_story_state(canon), _delta(chapter)
    )
    assert any(item["code"] == "state_reversion" for item in bad_report["violations"])

    chapter["state_transitions"][0]["from_value"] = []
    validate_generation_plan(canon, [chapter])
    good_report, _state_after = validate_state_delta(
        canon, chapter, initial_story_state(canon), _delta(chapter)
    )
    assert good_report == {"status": "passed", "violations": []}
