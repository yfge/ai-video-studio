import copy

import pytest
from app.services.story.story_novel_expected_delta import compile_expected_delta


def _plan():
    return {
        "required_event_ids": ["event-transfer"],
        "state_transitions": [
            {
                "subject_id": "mirror-core",
                "field": "owner_id",
                "from_value": "char-wen-lu",
                "to_value": "char-su-yan",
            }
        ],
        "location_transitions": [
            {
                "subject_id": "char-su-yan",
                "from_location_id": "loc-hall",
                "to_location_id": "loc-dock",
            }
        ],
        "knowledge_grants": [
            {
                "character_id": "char-su-yan",
                "fact_id": "fact-core-authentic",
                "source_event_id": "event-transfer",
            }
        ],
        "milestones_consumed": ["mile-core-transfer"],
        "open_threads": ["thread-core-origin"],
        "payoffs_due": ["thread-old-signal"],
    }


def test_expected_delta_is_compiled_only_from_plan_and_state_before():
    state = {"subjects": {"mirror-core": {"owner_id": "char-wen-lu"}}}
    delta = compile_expected_delta(_plan(), state)

    assert delta["occurred_event_ids"] == ["event-transfer"]
    assert delta["opened_thread_ids"] == ["thread-core-origin"]
    assert delta["resolved_thread_ids"] == ["thread-old-signal"]
    assert [item["contract_id"] for item in delta["proof_contracts"]] == [
        "event:event-transfer",
        "state:1",
        "location:1",
        "knowledge:1",
    ]
    assert delta["milestones_consumed"] == ["mile-core-transfer"]
    assert delta["opened_thread_ids"] == ["thread-core-origin"]
    assert delta["resolved_thread_ids"] == ["thread-old-signal"]
    assert delta["state_before_hash"]
    assert delta["delta_hash"]


def test_expected_delta_does_not_accept_or_retain_model_state_payload():
    plan = _plan()
    plan["model_state_delta"] = {
        "state_transitions": [{"subject_id": "future", "field": "dead"}]
    }
    original = copy.deepcopy(plan)

    delta = compile_expected_delta(plan, {"subjects": {}})

    assert "model_state_delta" not in delta
    assert plan == original
    assert all(
        item["value"].get("subject_id") != "future"
        for item in delta["proof_contracts"]
        if isinstance(item["value"], dict)
    )


def test_expected_delta_rejects_duplicate_contract_ids_and_thread_conflicts():
    duplicate = _plan()
    duplicate["required_event_ids"] = ["event-transfer", "event-transfer"]
    with pytest.raises(ValueError, match="事件 ID 重复"):
        compile_expected_delta(duplicate, {})

    conflict = _plan()
    conflict["payoffs_due"] = ["thread-core-origin"]
    with pytest.raises(ValueError, match="同时打开和回收"):
        compile_expected_delta(conflict, {})
