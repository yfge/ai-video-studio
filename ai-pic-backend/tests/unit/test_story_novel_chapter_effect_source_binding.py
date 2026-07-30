import pytest
from app.services.story.story_novel_chapter_effect_coverage import (
    stale_effect_refs,
    validate_effect_coverage,
)


def _contract(source_event_id="event-1-1"):
    return {
        "required_event_ids": ["event-1-1"],
        "state_transitions": [],
        "location_transitions": [],
        "knowledge_grants": [
            {
                "character_id": "char-a",
                "fact_id": "fact-a",
                "source_event_id": source_event_id,
            }
        ],
        "milestones_consumed": [],
    }


def _coverage():
    return [
        {
            "event_id": "event-1-1",
            "field_reviews": [],
            "no_persistent_effect": False,
            "rationale": "当前事件授予长期知识",
        }
    ]


def test_source_bound_knowledge_effect_is_completed_deterministically():
    result = validate_effect_coverage(_coverage(), _contract(), [], {"milestones": []})

    assert result["items"][0]["field_reviews"] == [
        {
            "subject_id": "char-a",
            "field": "knowledge",
            "disposition": "changed",
            "effect_refs": ["knowledge:1"],
            "reason": "由章节合同的 source_event_id 确定性绑定",
        }
    ]


def test_source_bound_knowledge_effect_is_relocated_to_contract_subject():
    coverage = _coverage()
    coverage[0]["field_reviews"] = [
        {
            "subject_id": "char-b",
            "field": "knowledge",
            "disposition": "changed",
            "effect_refs": ["knowledge:1"],
            "reason": "模型把同一事件的知识变化挂到了错误角色",
        }
    ]

    result = validate_effect_coverage(coverage, _contract(), [], {"milestones": []})

    reviews = result["items"][0]["field_reviews"]
    assert reviews[0]["effect_refs"] == []
    assert reviews[0]["disposition"] == "unchanged"
    assert reviews[1] == {
        "subject_id": "char-a",
        "field": "knowledge",
        "disposition": "changed",
        "effect_refs": ["knowledge:1"],
        "reason": "由章节合同的 source_event_id 确定性绑定",
    }


def test_effect_from_another_event_is_not_silently_reassigned():
    with pytest.raises(ValueError, match="typed effect"):
        validate_effect_coverage(
            _coverage(), _contract("event-1-2"), [], {"milestones": []}
        )


def test_ref_removed_by_contract_normalization_is_not_a_false_mismatch():
    raw = _contract()
    raw["location_transitions"] = [
        {
            "subject_id": "char-a",
            "from_location_id": "loc-a",
            "to_location_id": "loc-b",
        }
    ]
    coverage = _coverage()
    coverage[0]["field_reviews"].append(
        {
            "subject_id": "char-a",
            "field": "location",
            "disposition": "changed",
            "effect_refs": ["location:1"],
            "reason": "模型仍引用规范化前的移动",
        }
    )

    result = validate_effect_coverage(
        coverage,
        _contract(),
        [],
        {"milestones": []},
        stale_effect_refs=stale_effect_refs(raw, _contract(), {"milestones": []}),
    )

    review = next(
        item
        for item in result["items"][0]["field_reviews"]
        if item["field"] == "location"
    )
    assert review["disposition"] == "unchanged"
    assert review["effect_refs"] == []


def test_unambiguous_top_level_effect_ref_is_bound_to_typed_field_review():
    coverage = _coverage()
    coverage[0].update(field_reviews=[], effect_refs=["knowledge:1"])

    result = validate_effect_coverage(
        coverage,
        _contract(),
        [],
        {"milestones": []},
    )

    assert result["items"][0]["field_reviews"] == [
        {
            "subject_id": "char-a",
            "field": "knowledge",
            "disposition": "changed",
            "effect_refs": ["knowledge:1"],
            "reason": "当前事件授予长期知识",
        }
    ]


def test_unknown_top_level_effect_ref_remains_invalid():
    coverage = _coverage()
    coverage[0].update(field_reviews=[], effect_refs=["knowledge:99"])

    with pytest.raises(ValueError, match="项字段无效"):
        validate_effect_coverage(
            coverage,
            _contract(),
            [],
            {"milestones": []},
        )
