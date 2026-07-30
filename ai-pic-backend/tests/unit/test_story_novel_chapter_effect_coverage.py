import pytest
from app.services.story.story_novel_chapter_effect_coverage import (
    build_effect_review_contracts,
    coverage_checkpoint_valid,
    validate_effect_coverage,
)


def _canon():
    return {
        "entities": [
            {
                "id": "obj-contract",
                "kind": "object",
                "name": "试种契",
                "aliases": [],
            }
        ],
        "milestones": [],
    }


def _contract(with_transition=True):
    return {
        "required_event_ids": ["event-1-1"],
        "key_events": ["沈禾与里正签署试种契"],
        "state_transitions": (
            [
                {
                    "subject_id": "obj-contract",
                    "field": "status",
                    "from_value": "unsigned",
                    "to_value": "signed",
                    "reason": "双方签署",
                }
            ]
            if with_transition
            else []
        ),
        "location_transitions": [],
        "knowledge_grants": [],
        "milestones_consumed": [],
    }


def _reviews():
    return [
        {
            "event_id": "event-1-1",
            "required_field_reviews": [
                {"subject_id": "obj-contract", "field": "status"}
            ],
        }
    ]


def _coverage(disposition="changed", refs=None):
    refs = ["state:1"] if refs is None else refs
    return [
        {
            "event_id": "event-1-1",
            "field_reviews": [
                {
                    "subject_id": "obj-contract",
                    "field": "status",
                    "disposition": disposition,
                    "effect_refs": refs,
                    "reason": "签署使契约由未签转为已签",
                }
            ],
            "no_persistent_effect": not refs,
            "rationale": "签约是长期状态变化" if refs else "没有长期变化",
        }
    ]


def test_effect_review_contract_covers_named_subject_current_fields():
    result = build_effect_review_contracts(
        _contract(),
        _canon(),
        {
            "subjects": {
                "obj-contract": {
                    "status": "unsigned",
                    "owner_id": "char-village",
                    "possessions": [],
                }
            }
        },
    )

    assert result == [
        {
            "event_id": "event-1-1",
            "required_field_reviews": [
                {"subject_id": "obj-contract", "field": "owner_id"},
                {"subject_id": "obj-contract", "field": "status"},
            ],
        }
    ]


def test_signed_contract_effect_is_bound_and_checkpointed():
    coverage = _coverage()
    coverage[0]["no_persistent_effect"] = True
    result = validate_effect_coverage(coverage, _contract(), _reviews(), _canon())
    chapter = {"required_event_ids": ["event-1-1"], "effect_coverage": result}

    assert result["items"][0]["field_reviews"][0]["effect_refs"] == ["state:1"]
    assert result["items"][0]["no_persistent_effect"] is False
    assert coverage_checkpoint_valid(chapter)


def test_missing_field_review_fails_instead_of_silently_dropping_contract_state():
    coverage = _coverage()
    coverage[0]["field_reviews"] = []

    with pytest.raises(ValueError, match="未审查当前事件涉及的状态字段"):
        validate_effect_coverage(coverage, _contract(), _reviews(), _canon())


def test_unclaimed_typed_effect_fails_closed():
    with pytest.raises(ValueError, match="未绑定 typed effects"):
        validate_effect_coverage(
            _coverage("unchanged", []), _contract(), _reviews(), _canon()
        )


def test_no_effect_event_must_still_review_named_current_field():
    result = validate_effect_coverage(
        _coverage("unchanged", []), _contract(False), _reviews(), _canon()
    )

    assert result["items"][0]["no_persistent_effect"] is True


def test_matching_milestone_alias_is_bound_without_a_second_model_choice():
    canon = _canon()
    canon["milestones"] = [
        {
            "id": "mile-sign",
            "outcomes": [
                {
                    "subject_id": "obj-contract",
                    "field": "status",
                    "operator": "eq",
                    "value": "signed",
                }
            ],
        }
    ]
    contract = {**_contract(), "milestones_consumed": ["mile-sign"]}

    result = validate_effect_coverage(_coverage(), contract, _reviews(), canon)

    assert result["items"][0]["field_reviews"][0]["effect_refs"] == [
        "state:1",
        "milestone:mile-sign:obj-contract:status",
    ]


def test_contains_milestone_alias_matches_complete_list_transition():
    canon = {
        "entities": [{"id": "char-a", "kind": "character", "name": "甲"}],
        "milestones": [
            {
                "id": "mile-right",
                "outcomes": [
                    {
                        "subject_id": "char-a",
                        "field": "permissions",
                        "operator": "contains",
                        "value": "trial-right",
                    }
                ],
            }
        ],
    }
    contract = {
        "required_event_ids": ["event-1-1"],
        "state_transitions": [
            {
                "subject_id": "char-a",
                "field": "permissions",
                "from_value": [],
                "to_value": ["trial-right"],
                "reason": "获得权利",
            }
        ],
        "location_transitions": [],
        "knowledge_grants": [],
        "milestones_consumed": ["mile-right"],
    }
    reviews = [
        {
            "event_id": "event-1-1",
            "required_field_reviews": [
                {"subject_id": "char-a", "field": "permissions"}
            ],
        }
    ]
    coverage = [
        {
            "event_id": "event-1-1",
            "field_reviews": [
                {
                    "subject_id": "char-a",
                    "field": "permissions",
                    "disposition": "changed",
                    "effect_refs": ["state:1"],
                    "reason": "当前事件获得权利",
                }
            ],
            "no_persistent_effect": False,
            "rationale": "权利持续有效",
        }
    ]

    result = validate_effect_coverage(coverage, contract, reviews, canon)

    assert result["items"][0]["field_reviews"][0]["effect_refs"] == [
        "state:1",
        "milestone:mile-right:char-a:permissions",
    ]


def test_different_milestone_outcome_is_not_treated_as_an_alias():
    canon = _canon()
    canon["milestones"] = [
        {
            "id": "mile-other",
            "outcomes": [
                {
                    "subject_id": "obj-contract",
                    "field": "status",
                    "operator": "eq",
                    "value": "archived",
                }
            ],
        }
    ]
    contract = {**_contract(), "milestones_consumed": ["mile-other"]}

    with pytest.raises(ValueError, match="未绑定 typed effects"):
        validate_effect_coverage(_coverage(), contract, _reviews(), canon)
