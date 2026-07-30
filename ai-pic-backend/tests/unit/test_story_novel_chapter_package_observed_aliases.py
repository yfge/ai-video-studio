import pytest
from app.services.story.story_novel_chapter_effect_coverage import (
    validate_effect_coverage,
)
from app.services.story.story_novel_chapter_package_normalization import (
    normalize_missing_contract_fields,
    repairable_contract_issues,
)


def test_execution_enum_aliases_normalize_before_repair():
    for phase, time_scope in (
        ("active", "short"),
        ("progressive", "short"),
        ("ongoing", "day"),
    ):
        contract = {
            "execution_contracts": [
                {
                    "event_id": "event-1-1",
                    "action_phase": phase,
                    "time_scope": time_scope,
                    "effort": "medium",
                }
            ]
        }

        result = normalize_missing_contract_fields(contract, {"entities": []})

        assert result["execution_contracts"][0]["action_phase"] == "progress"
        assert result["execution_contracts"][0]["time_scope"] == "same_day"
        assert result["execution_contracts"][0]["effort"] == "moderate"
        assert repairable_contract_issues(result) == []


def test_short_effect_refs_normalize_without_weakening_event_binding():
    contract = {
        "required_event_ids": ["event-1-1"],
        "state_transitions": [
            {
                "subject_id": "obj-contract",
                "field": "status",
                "from_value": "unsigned",
                "to_value": "signed",
            }
        ],
        "location_transitions": [
            {
                "subject_id": "char-a",
                "from_location_id": "loc-home",
                "to_location_id": "loc-field",
            }
        ],
        "knowledge_grants": [
            {
                "character_id": "char-a",
                "fact_id": "fact-soil",
                "source_event_id": "event-1-1",
            }
        ],
    }
    coverage = [
        {
            "event_id": "event-1-1",
            "field_reviews": [
                {
                    "subject_id": "obj-contract",
                    "field": "status",
                    "disposition": "changed",
                    "effect_refs": ["S1"],
                    "reason": "契约完成签署",
                },
                {
                    "subject_id": "char-a",
                    "field": "location",
                    "disposition": "changed",
                    "effect_refs": ["L1"],
                    "reason": "抵达田地",
                },
                {
                    "subject_id": "char-a",
                    "field": "knowledge",
                    "disposition": "changed",
                    "effect_refs": ["K1"],
                    "reason": "现场获知土壤情况",
                },
            ],
            "no_persistent_effect": False,
            "rationale": "当前事件产生三项长期变化",
        }
    ]
    reviews = [
        {
            "event_id": "event-1-1",
            "required_field_reviews": [
                {"subject_id": "obj-contract", "field": "status"},
                {"subject_id": "char-a", "field": "location"},
                {"subject_id": "char-a", "field": "knowledge"},
            ],
        }
    ]

    result = validate_effect_coverage(coverage, contract, reviews, {"milestones": []})

    assert [
        review["effect_refs"] for review in result["items"][0]["field_reviews"]
    ] == [["state:1"], ["location:1"], ["knowledge:1"]]


def test_atomic_milestone_outcomes_inherit_one_proven_event():
    contract = {
        "required_event_ids": ["event-1-1", "event-1-2", "event-1-3"],
        "state_transitions": [
            {
                "subject_id": "char-main",
                "field": "permissions",
                "from_value": [],
                "to_value": ["trial-right"],
            },
            {
                "subject_id": "object-contract",
                "field": "status",
                "from_value": "not-signed",
                "to_value": "signed",
            },
        ],
        "location_transitions": [
            {
                "subject_id": "char-main",
                "from_location_id": "loc-home",
                "to_location_id": "loc-village",
            }
        ],
        "knowledge_grants": [
            {
                "character_id": "char-main",
                "fact_id": "fact-land",
                "source_event_id": "event-1-2",
            },
            {
                "character_id": "char-main",
                "fact_id": "fact-water",
                "source_event_id": "event-1-3",
            },
        ],
        "milestones_consumed": ["mile-1"],
    }
    canon = {
        "milestones": [
            {
                "id": "mile-1",
                "outcomes": [
                    {
                        "subject_id": "char-main",
                        "field": "permissions",
                        "operator": "contains",
                        "value": "trial-right",
                    },
                    {
                        "subject_id": "object-contract",
                        "field": "status",
                        "operator": "eq",
                        "value": "signed",
                    },
                    {
                        "subject_id": "object-contract",
                        "field": "owner_id",
                        "operator": "eq",
                        "value": "char-main",
                    },
                ],
            }
        ]
    }
    coverage = [
        _row(
            "event-1-1",
            [
                _review("char-main", "permissions", ["state:1"]),
                _review("char-main", "location", ["location:1"]),
            ],
        ),
        _row(
            "event-1-2",
            [_review("char-main", "knowledge", ["knowledge:1"])],
        ),
        _row(
            "event-1-3",
            [_review("char-main", "knowledge", ["knowledge:2"])],
        ),
    ]

    result = validate_effect_coverage(coverage, contract, [], canon)

    first_refs = {
        ref
        for review in result["items"][0]["field_reviews"]
        for ref in review["effect_refs"]
    }
    assert first_refs == {
        "state:1",
        "state:2",
        "location:1",
        "milestone:mile-1:char-main:permissions",
        "milestone:mile-1:object-contract:status",
        "milestone:mile-1:object-contract:owner_id",
    }


def test_atomic_milestone_without_any_event_owner_still_fails_closed():
    contract = {
        "required_event_ids": ["event-1-1"],
        "state_transitions": [],
        "location_transitions": [],
        "knowledge_grants": [],
        "milestones_consumed": ["mile-1"],
    }
    outcome = dict(
        subject_id="object-contract", field="status", operator="eq", value="signed"
    )
    canon = {"milestones": [{"id": "mile-1", "outcomes": [outcome]}]}

    with pytest.raises(ValueError, match="未绑定 typed effects"):
        validate_effect_coverage([_row("event-1-1", [])], contract, [], canon)


def _review(subject_id: str, field: str, refs: list[str]) -> dict:
    return {
        "subject_id": subject_id,
        "field": field,
        "disposition": "changed" if refs else "unchanged",
        "effect_refs": refs,
        "reason": "当前事件的持久变化",
    }


def _row(event_id: str, reviews: list[dict]) -> dict:
    return {
        "event_id": event_id,
        "field_reviews": reviews,
        "no_persistent_effect": not any(review["effect_refs"] for review in reviews),
        "rationale": "逐事件复核结果",
    }
