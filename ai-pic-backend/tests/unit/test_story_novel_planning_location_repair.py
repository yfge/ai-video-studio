from app.services.story.story_novel_ai_prompts import planning_prompt
from app.services.story.story_novel_location_rules import ABSENT_OBJECT_STATUS_LITERALS
from app.services.story.story_novel_plan_repair import _repair_context
from app.services.story.story_novel_planning_phases import _plan_repair_prompt


def _canon():
    return {
        "entities": [
            {"id": "seal", "kind": "object"},
            {"id": "sample", "kind": "object"},
            {"id": "cen-ye", "kind": "character"},
        ],
        "initial_state": {
            "seal": {"status": "未签发", "location": None, "owner_id": None},
            "sample": {"status": "不存在", "location": None},
            "cen-ye": {"permissions": []},
        },
        "milestones": [
            {
                "id": "mile-seal-opened",
                "planned_position": 1,
                "repeatable": False,
                "outcomes": [
                    {
                        "subject_id": "seal",
                        "field": "status",
                        "operator": "eq",
                        "value": "opened",
                    }
                ],
            }
        ],
    }


def test_planning_prompt_uses_the_runtime_absence_literals():
    prompt = planning_prompt(planning_contract={}, canon=_canon())

    for value in (
        '"不存在"',
        '"尚未存在"',
        '"尚未创建"',
        '"未创建"',
        '"absent"',
        '"not-created"',
        '"not-yet-created"',
    ):
        assert value in prompt
    assert "未发现”“未找到”“未签发”“未采集”都不表示对象不存在" in prompt
    assert "Canon 中已经定义的空数组 [] 是精确旧值" in prompt


def test_repair_exposes_exact_unlocated_object_and_empty_array_states():
    context = _repair_context(
        '{"chapters":[]}',
        "地点起点不连续；cen-ye permissions 旧值错误",
        _canon(),
        {"chapters": []},
        None,
    )
    repair = _plan_repair_prompt(
        "原始提示",
        '{"chapters":[]}',
        "地点起点不连续；cen-ye permissions 旧值错误",
        [1],
        canon=_canon(),
        frozen_spec={"chapters": []},
    )

    assert context["unlocated_object_initial_states"] == [
        {
            "subject_id": "sample",
            "status": "不存在",
            "status_is_defined": True,
            "owner_id": None,
            "owner_id_is_defined": False,
            "location": None,
            "location_is_defined": True,
        },
        {
            "subject_id": "seal",
            "status": "未签发",
            "status_is_defined": True,
            "owner_id": None,
            "owner_id_is_defined": True,
            "location": None,
            "location_is_defined": True,
        },
    ]
    assert context["authoritative_initial_state"]["cen-ye"]["permissions"] == []
    assert context["object_location_contract"] == {
        "absence_status_literals": list(ABSENT_OBJECT_STATUS_LITERALS),
        "non_absence_status_examples": ["未发现", "未找到", "未签发", "未采集"],
    }
    assert context["state_value_contract"] == {
        "undefined_field_from_value": None,
        "defined_empty_array_from_value": [],
        "copy_authoritative_values_without_coercion": True,
    }
    assert context["derived_state_contract"] == {
        "possessions": "derived_from_object_owner_id_never_transition_directly"
    }
    assert context["milestone_outcome_contracts"] == [
        {
            "id": "mile-seal-opened",
            "planned_position": 1,
            "outcomes": [
                {
                    "subject_id": "seal",
                    "field": "status",
                    "operator": "eq",
                    "value": "opened",
                }
            ],
        }
    ]
    assert '"unlocated_object_initial_states"' in repair
    assert '"permissions":[]' in repair
    assert '"owner_id":null' in repair
    assert "已经定义的空数组 [] 是精确旧值" in repair
    assert "未发现”“未找到”“未签发”“未采集”均表示对象已存在或状态未定义" in repair
    assert "禁止猜测落点或接收者" in repair
    assert "禁止直接写 possessions state_transition" in repair
    assert "opened 不能改成已开启" in repair
