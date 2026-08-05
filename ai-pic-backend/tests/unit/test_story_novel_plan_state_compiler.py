import pytest
from app.services.story.story_novel_canon_service import validate_generation_plan
from app.services.story.story_novel_plan_state_compiler import compile_plan_state
from tests.unit.test_story_novel_longform import _canon, _plan_row


def test_service_compiles_state_origins_and_preconditions_from_current_state():
    row = _plan_row(1)
    row["preconditions"] = [
        {
            "subject_id": "char-a",
            "field": "status",
            "operator": "eq",
            "value": "模型猜错的旧值",
        }
    ]
    row["state_transitions"] = [
        {
            "subject_id": "char-a",
            "field": "status",
            "from_value": "模型猜错的旧值",
            "to_value": "警觉",
            "reason": "发现线索",
        }
    ]

    compiled = compile_plan_state(_canon(), [row])[0]

    assert compiled["state_transitions"][0]["from_value"] == "守规"
    assert compiled["preconditions"] == [
        {
            "subject_id": "char-a",
            "field": "status",
            "operator": "eq",
            "value": "守规",
        }
    ]
    assert compiled["state_compiler"]["version"] == 1


def test_service_compiles_location_origin_instead_of_trusting_model_from():
    canon = _canon()
    canon["entities"].append(
        {
            "id": "loc-next",
            "kind": "location",
            "name": "下一站",
            "aliases": [],
            "attributes": {},
        }
    )
    row = _plan_row(1)
    row["location_transitions"] = [
        {
            "subject_id": "char-a",
            "from_location_id": "loc-next",
            "to_location_id": "loc-next",
            "means": "步行",
        }
    ]

    compiled = compile_plan_state(canon, [row])[0]

    assert compiled["location_transitions"] == [
        {
            "subject_id": "char-a",
            "from_location_id": "loc-gate",
            "to_location_id": "loc-next",
            "means": "步行",
        }
    ]


def test_service_compiles_knowledge_boundary_from_grants():
    row = _plan_row(1)
    row["knowledge_grants"] = [
        {
            "character_id": "char-a",
            "fact_id": "fact-event-1-1",
            "source_event_id": "event-1",
        }
    ]

    compiled = compile_plan_state(_canon(), [row])[0]

    assert compiled["preconditions"] == [
        {
            "subject_id": "char-a",
            "field": "knowledge",
            "operator": "not_contains",
            "value": "fact-event-1-1",
        }
    ]


def test_service_compiles_consumed_milestone_outcomes_into_typed_effects():
    canon = _canon()
    canon["entities"].extend(
        [
            {
                "id": "org-cooperative",
                "kind": "organization",
                "name": "柳溪合作社",
                "aliases": [],
                "attributes": {},
            },
            {
                "id": "loc-field",
                "kind": "location",
                "name": "三亩田",
                "aliases": [],
                "attributes": {},
            },
        ]
    )
    canon["initial_state"]["org-cooperative"] = {
        "status": "筹备中",
        "permissions": [],
    }
    canon["milestones"] = [
        {
            "id": "mile-cooperative-active",
            "label": "合作社正式成立",
            "planned_position": 1,
            "repeatable": False,
            "outcomes": [
                {
                    "subject_id": "org-cooperative",
                    "field": "status",
                    "operator": "eq",
                    "value": "active",
                },
                {
                    "subject_id": "org-cooperative",
                    "field": "permissions",
                    "operator": "contains",
                    "value": "public-seal",
                },
                {
                    "subject_id": "char-a",
                    "field": "knowledge",
                    "operator": "contains",
                    "value": "fact-cooperative-active",
                },
                {
                    "subject_id": "char-a",
                    "field": "location",
                    "operator": "eq",
                    "value": "loc-field",
                },
            ],
        }
    ]
    row = _plan_row(1)
    row["milestones_consumed"] = ["mile-cooperative-active"]

    compiled = compile_plan_state(canon, [row])[0]

    assert [item["to_value"] for item in compiled["state_transitions"]] == [
        "active",
        ["public-seal"],
    ]
    assert compiled["knowledge_grants"] == [
        {
            "character_id": "char-a",
            "fact_id": "fact-cooperative-active",
            "source_event_id": "event-1",
        }
    ]
    assert compiled["location_transitions"] == [
        {
            "subject_id": "char-a",
            "from_location_id": "loc-gate",
            "to_location_id": "loc-field",
            "means": "Canon milestone mile-cooperative-active",
        }
    ]
    validate_generation_plan(canon, [compiled])


def test_service_rejects_unknown_milestone_owner_target_defensively():
    canon = _canon()
    canon["milestones"] = [
        {
            "id": "mile-invalid-owner",
            "label": "交给不存在的人",
            "planned_position": 1,
            "repeatable": False,
            "outcomes": [
                {
                    "subject_id": "char-a",
                    "field": "owner_id",
                    "operator": "eq",
                    "value": "char-not-exist",
                }
            ],
        }
    ]
    row = _plan_row(1)
    row["milestones_consumed"] = ["mile-invalid-owner"]

    with pytest.raises(ValueError, match="owner_id 指向非法所有者"):
        compile_plan_state(canon, [row])


def test_service_drops_knowledge_array_only_when_exact_grants_cover_additions():
    row = _plan_row(1)
    row["knowledge_grants"] = [
        {
            "character_id": "char-a",
            "fact_id": "fact-new",
            "source_event_id": "event-1",
        }
    ]
    row["state_transitions"] = [
        {
            "subject_id": "char-a",
            "field": "knowledge",
            "from_value": [],
            "to_value": ["fact-new"],
            "reason": "重复表示知识授予",
        }
    ]

    compiled = compile_plan_state(_canon(), [row])[0]

    assert compiled["state_transitions"] == []
    validate_generation_plan(_canon(), [compiled])


def test_service_keeps_unbound_knowledge_array_for_strict_gate_rejection():
    row = _plan_row(1)
    row["state_transitions"] = [
        {
            "subject_id": "char-a",
            "field": "knowledge",
            "from_value": [],
            "to_value": ["fact-without-source"],
            "reason": "没有对应知识授予",
        }
    ]

    compiled = compile_plan_state(_canon(), [row])[0]

    with pytest.raises(ValueError, match="knowledge 不能写入 state_transitions"):
        validate_generation_plan(_canon(), [compiled])


def test_service_drops_milestone_knowledge_array_after_compiling_missing_grant():
    canon = _canon()
    canon["milestones"] = [
        {
            "id": "mile-knowledge",
            "label": "公开事实",
            "planned_position": 1,
            "repeatable": False,
            "outcomes": [
                {
                    "subject_id": "char-a",
                    "field": "knowledge",
                    "operator": "contains",
                    "value": "fact-milestone",
                }
            ],
        }
    ]
    row = _plan_row(1)
    row["milestones_consumed"] = ["mile-knowledge"]
    row["state_transitions"] = [
        {
            "subject_id": "char-a",
            "field": "knowledge",
            "from_value": [],
            "to_value": ["fact-milestone"],
            "reason": "模型错误地用数组表达知识",
        }
    ]

    compiled = compile_plan_state(canon, [row])[0]

    assert compiled["state_transitions"] == []
    assert compiled["knowledge_grants"][0]["fact_id"] == "fact-milestone"
    validate_generation_plan(canon, [compiled])
