import json

import pytest
from app.services.story.story_novel_canon_service import (
    CANON_GATE_VERSION,
    normalize_canon,
    validate_generation_plan,
)
from app.services.story.story_novel_planning_phases import _parse_canon
from tests.unit.test_story_novel_longform import _canon, _plan_row


def _v2_revision(revision, row):
    canon = normalize_canon(_canon())
    revision.generation_plan = {
        "schema": "story_novel_generation_plan.v2",
        "version": 2,
        "status": "ready",
        "canon": canon,
        "canon_hash": canon["canon_hash"],
        "chapter_count": 1,
        "target_chars": 3000,
        "chapters": [row],
    }
    revision.chapter_count = 1
    return canon


def _body():
    return json.dumps(
        {
            "title": "第一章",
            "content_text": "第一日，" + "正文" * 1500,
            "summary": "主角发现裂缝",
            "plot_delta": {"key_events": ["发现线索"]},
        },
        ensure_ascii=False,
    )


def _delta(*, events=None, premature=None, world_rule_violations=None):
    occurred = events if events is not None else ["event-1"]
    future = premature or []
    quote = "正文正文正文正文"
    return json.dumps(
        {
            "occurred_event_ids": occurred,
            "premature_future_event_ids": future,
            "state_transitions": [],
            "knowledge_grants": [],
            "location_transitions": [],
            "milestones_consumed": [],
            "opened_thread_ids": [],
            "resolved_thread_ids": [],
            "world_rule_violations": world_rule_violations or [],
            "evidence": {event_id: quote for event_id in occurred + future},
            "timeline_evidence": (
                {"time-1": f"第一日……{quote}"} if "event-1" in occurred else {}
            ),
        },
        ensure_ascii=False,
    )


def test_model_canon_defaults_only_a_missing_current_gate_version():
    payload = _canon()
    payload.pop("gate_version")

    canon, error = _parse_canon(json.dumps(payload, ensure_ascii=False))

    assert error is None
    assert canon["gate_version"] == CANON_GATE_VERSION

    payload["gate_version"] = 0
    canon, error = _parse_canon(json.dumps(payload, ensure_ascii=False))
    assert canon is None
    assert f"gate_version 必须至少为 {CANON_GATE_VERSION}" in error


def test_parse_canon_drops_a_timeline_time_borrowed_from_another_event():
    dated_event = "第一日，发现线索"
    undated_event = "主角把线索封入证物袋"
    payload = _canon()
    payload["timeline"].append(
        {
            "id": "time-borrowed",
            "label": undated_event,
            "order": 2,
            "story_time": "第一日",
            "immutable": True,
            "source_chapter_position": 1,
            "source_key_event": undated_event,
        }
    )
    contract = {
        "story_seed": {
            "structured_outline": {
                "chapters": [
                    {
                        "position": 1,
                        "key_events": [dated_event, undated_event],
                    }
                ]
            }
        }
    }

    canon, error = _parse_canon(
        json.dumps(payload, ensure_ascii=False),
        contract,
    )

    assert error is None
    assert [item["id"] for item in canon["timeline"]] == ["time-1"]


def test_normalize_canon_still_rejects_an_unsourced_timeline_time():
    payload = _canon()
    payload["timeline"].append(
        {
            "id": "time-invented",
            "label": "主角把线索封入证物袋",
            "order": 2,
            "story_time": "第一日",
            "immutable": True,
            "source_chapter_position": 1,
            "source_key_event": "主角把线索封入证物袋",
        }
    )

    with pytest.raises(
        ValueError,
        match="immutable timeline story_time 未逐字来自来源事件: time-invented",
    ):
        normalize_canon(payload)


def test_parse_canon_keeps_a_source_literal_without_a_time_word_list():
    event = "主角在T+3发现线索"
    payload = _canon()
    payload["timeline"][0].update(
        {"label": event, "story_time": "T+3", "source_key_event": event}
    )
    contract = {
        "story_seed": {
            "structured_outline": {"chapters": [{"position": 1, "key_events": [event]}]}
        }
    }

    canon, error = _parse_canon(json.dumps(payload, ensure_ascii=False), contract)

    assert error is None
    assert [item["id"] for item in canon["timeline"]] == ["time-1"]


def test_plan_linter_rejects_duplicate_once_only_milestone():
    canon_raw = _canon()
    canon_raw["milestones"] = [
        {
            "id": "mile-choice",
            "label": "作出选择",
            "planned_position": None,
            "repeatable": False,
        }
    ]
    canon = normalize_canon(canon_raw)
    rows = [_plan_row(1), _plan_row(2)]
    rows[0]["milestones_consumed"] = ["mile-choice"]
    rows[1]["milestones_consumed"] = ["mile-choice"]

    with pytest.raises(ValueError, match="里程碑重复消费"):
        validate_generation_plan(canon, rows)


def test_plan_linter_applies_knowledge_before_later_preconditions():
    canon = normalize_canon(_canon())
    rows = [_plan_row(1), _plan_row(2)]
    rows[0]["knowledge_grants"] = [
        {
            "character_id": "char-a",
            "fact_id": "fact-1",
            "source_event_id": "event-1",
        }
    ]
    rows[1]["preconditions"] = [
        {
            "subject_id": "char-a",
            "field": "knowledge",
            "operator": "contains",
            "value": "fact-1",
        }
    ]
    rows[1]["forbidden_event_ids"] = ["event-1"]

    validate_generation_plan(canon, rows)

    rows[1]["forbidden_event_ids"] = ["event-3"]
    with pytest.raises(ValueError, match="禁止事件尚未发生"):
        validate_generation_plan(canon, rows)


def test_plan_linter_rejects_future_ownership_in_initial_state():
    canon_raw = _canon()
    canon_raw["entities"].append(
        {
            "id": "obj-key",
            "kind": "object",
            "name": "唯一钥匙",
            "aliases": [],
            "attributes": {},
        }
    )
    canon_raw["initial_state"]["obj-key"] = {
        "location": "loc-gate",
        "owner_id": "char-a",
        "status": "已移交",
    }
    canon = normalize_canon(canon_raw)
    row = _plan_row(1)
    row["preconditions"] = [
        {
            "subject_id": "obj-key",
            "field": "owner_id",
            "operator": "eq",
            "value": None,
        }
    ]
    row["state_transitions"] = [
        {
            "subject_id": "obj-key",
            "field": "owner_id",
            "from_value": None,
            "to_value": "char-a",
            "reason": "第一章才完成移交",
        }
    ]

    with pytest.raises(ValueError, match="第 1 章前置状态不连续"):
        validate_generation_plan(canon, [row])
