import pytest
from app.services.story.story_novel_chapter_package_normalization import (
    normalize_missing_contract_fields,
    repairable_contract_issues,
)


def test_observed_package_aliases_normalize_without_inventing_effects():
    contract = {
        "knowledge_grants": [
            {
                "character_id": character_id,
                "knowledge": ["fact-waterwheel-repaired-limited"],
            }
            for character_id in ("char-he", "char-yan")
        ],
        "location_transitions": [
            {"entity_id": "obj-waterwheel", "to_location": "loc-south-slope"}
        ],
        "execution_contracts": [
            {
                "event_id": "event-28-1",
                "action_phase": "instant",
                "time_scope": "specific",
                "effort": "light",
                "actor_ids": ["char-he", "char-yan"],
                "knowledge_fact_ids": ["fact-waterwheel-repaired-limited"],
            }
        ],
    }
    canon = {
        "entities": [
            {"id": character_id, "kind": "character"}
            for character_id in ("char-he", "char-yan")
        ]
    }

    result = normalize_missing_contract_fields(contract, canon)

    assert result["execution_contracts"][0]["time_scope"] == "specific"
    assert result["knowledge_grants"] == [
        {
            "character_id": character_id,
            "fact_id": "fact-waterwheel-repaired-limited",
            "source_event_id": "event-28-1",
        }
        for character_id in ("char-he", "char-yan")
    ]
    assert result["location_transitions"] == [
        {
            "subject_id": "obj-waterwheel",
            "to_location_id": "loc-south-slope",
        }
    ]
    assert repairable_contract_issues(result) == [
        "execution_contracts[0].time_scope='specific' 无效；必须选择 "
        "instant/same_day/multi_day/unspecified",
        "location_transitions[0].means 缺少真实移动过程",
        "location_transitions[0].from_location_id 缺失；必须显式提供起点，"
        "若为 null 还必须同章提供该物件唯一 status 创建转换",
    ]


def test_ambiguous_knowledge_source_is_not_invented():
    contract = {
        "knowledge_grants": [{"character_id": "char-he", "knowledge": ["fact-shared"]}],
        "execution_contracts": [
            {
                "event_id": event_id,
                "action_phase": "instant",
                "time_scope": "unspecified",
                "effort": "light",
                "knowledge_fact_ids": ["fact-shared"],
            }
            for event_id in ("event-1", "event-2")
        ],
    }

    result = normalize_missing_contract_fields(contract, {"entities": []})

    assert result["knowledge_grants"] == [
        {"character_id": "char-he", "fact_id": "fact-shared"}
    ]
    assert repairable_contract_issues(result) == [
        "knowledge_grants[0].source_event_id 缺失，禁止服务端猜测"
    ]


def test_grouped_fact_aliases_preserve_explicit_source_and_report_conflicts():
    facts = ["fact-waterwheel-steady", "fact-waterwheel-limited"]
    contract = {
        "knowledge_grants": [
            {
                "character_id": character_id,
                "knowledge_ids": facts,
                "fact_ids": facts,
                "source_event_id": source_event_id,
            }
            for character_id, source_event_id in (
                ("char-he", "event-28-1"),
                ("char-yan", "event-28-2"),
            )
        ],
        "execution_contracts": [
            {
                "event_id": event_id,
                "action_phase": "instant",
                "time_scope": "same_day",
                "effort": "light",
                "knowledge_fact_ids": [fact_id],
            }
            for event_id, fact_id in (
                ("event-28-1", facts[0]),
                ("event-28-2", facts[1]),
            )
        ],
    }

    result = normalize_missing_contract_fields(contract, {"entities": []})

    assert result["knowledge_grants"] == [
        {
            "character_id": character_id,
            "source_event_id": source_event_id,
            "fact_id": fact_id,
        }
        for character_id, source_event_id in (
            ("char-he", "event-28-1"),
            ("char-yan", "event-28-2"),
        )
        for _, fact_id in (
            ("event-28-1", facts[0]),
            ("event-28-2", facts[1]),
        )
    ]
    assert repairable_contract_issues(result) == [
        "knowledge_grants[1].source_event_id='event-28-1' 与 "
        "execution_contracts 冲突；fact_id='fact-waterwheel-limited' "
        "只能绑定 event-28-2",
        "knowledge_grants[2].source_event_id='event-28-2' 与 "
        "execution_contracts 冲突；fact_id='fact-waterwheel-steady' "
        "只能绑定 event-28-1",
    ]


def test_missing_character_is_not_inferred_from_event_actor():
    contract = {
        "knowledge_grants": [{"fact_id": "fact-seed", "source_event_id": "event-11-1"}],
        "execution_contracts": [
            {
                "event_id": "event-11-1",
                "action_phase": "instant",
                "time_scope": "unspecified",
                "effort": "light",
                "actor_ids": ["char-he"],
                "knowledge_fact_ids": ["fact-seed"],
            }
        ],
    }

    result = normalize_missing_contract_fields(contract, {"entities": []})

    assert "character_id" not in result["knowledge_grants"][0]
    assert repairable_contract_issues(result) == [
        "knowledge_grants[0].character_id 缺失，禁止服务端猜测"
    ]


@pytest.mark.parametrize(
    ("from_key", "to_key"), [("from_location", "to_location"), ("from", "to")]
)
def test_explicit_nullable_origin_alias_remains_explicit(from_key, to_key):
    contract = {
        "location_transitions": [
            {
                "entity_id": "obj-waterwheel",
                from_key: None,
                to_key: "loc-south-slope",
                "means": "在南坡完成组装",
            }
        ]
    }

    result = normalize_missing_contract_fields(contract, {"entities": []})

    assert result["location_transitions"][0]["from_location_id"] is None


@pytest.mark.parametrize(
    ("from_key", "to_key"), [("from_status", "to_status"), ("from", "to")]
)
def test_status_aliases_normalize_but_missing_creation_reason_stays_invalid(
    from_key, to_key
):
    contract = {
        "state_transitions": [
            {
                "subject_id": "obj-waterwheel",
                **({"field": "status"} if from_key == "from" else {}),
                from_key: None,
                to_key: "operational",
            }
        ],
        "location_transitions": [
            {
                "subject_id": "obj-waterwheel",
                "from_location_id": None,
                "to_location_id": "loc-south-slope",
                "means": "在南坡完成组装",
            }
        ],
    }

    result = normalize_missing_contract_fields(contract, {"entities": []})

    assert result["state_transitions"] == [
        {
            "subject_id": "obj-waterwheel",
            "field": "status",
            "from_value": None,
            "to_value": "operational",
        }
    ]
    assert repairable_contract_issues(result) == [
        "state_transitions 对 obj-waterwheel 的创建转换必须包含显式 "
        "from_value、to_value 和非空 reason"
    ]


def test_all_invalid_execution_enums_are_reported_before_single_repair():
    contract = {
        "execution_contracts": [
            {
                "event_id": "event-28-1",
                "action_phase": "observation",
                "time_scope": "unspecified",
                "effort": "medium",
            }
        ]
    }

    assert repairable_contract_issues(contract) == [
        "execution_contracts[0].action_phase='observation' 无效；必须选择 "
        "start/progress/complete/instant",
        "execution_contracts[0].effort='medium' 无效；必须选择 "
        "none/light/moderate/heavy/unspecified",
    ]
