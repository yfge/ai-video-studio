import copy
import json

import pytest
from app.schemas.story_novel_longform import StoryNovelGenerationPlan
from app.services.story.story_novel_canon_service import (
    normalize_canon,
    validate_generation_plan,
)
from app.services.story.story_novel_evidence_rules import timeline_evidence_violations
from app.services.story.story_novel_length_service import generation_plan_hash
from pydantic import ValidationError
from tests.unit.test_story_novel_longform import _canon, _plan_row


def _timeline_row() -> dict:
    return _plan_row(1)


def test_v2_chapter_schema_requires_explicit_timeline_event_bindings():
    row = _plan_row(1)
    row.pop("timeline_event_bindings")

    with pytest.raises(ValidationError, match="timeline_event_bindings"):
        StoryNovelGenerationPlan.model_validate({"chapters": [row]})


@pytest.mark.parametrize(
    "mutation",
    [
        lambda row: row.update(required_event_ids=[""]),
        lambda row: row.update(timeline_event_bindings={"time-1": ""}),
        lambda row: row.update(timeline_event_bindings={"": "event-1"}),
    ],
)
def test_v2_chapter_schema_rejects_blank_event_or_binding_ids(mutation):
    row = _timeline_row()
    mutation(row)

    with pytest.raises(ValidationError, match="non-blank"):
        StoryNovelGenerationPlan.model_validate({"chapters": [row]})


def test_plan_validator_rejects_blank_event_id_without_schema_parsing():
    row = _timeline_row()
    row["required_event_ids"] = [""]
    row["timeline_event_bindings"] = {"time-1": ""}

    with pytest.raises(ValueError, match="包含空 ID"):
        validate_generation_plan(normalize_canon(_canon()), [row])


@pytest.mark.parametrize(
    ("bindings", "message"),
    [
        ({}, "时间线缺少事件绑定"),
        (
            {"time-1": "event-1", "time-unknown": "event-1"},
            "时间线包含无效事件绑定",
        ),
        ({"time-1": "event-other"}, "时间线绑定非本章事件"),
    ],
)
def test_plan_rejects_missing_extra_or_non_current_timeline_bindings(bindings, message):
    row = _timeline_row()
    row["timeline_event_bindings"] = bindings

    with pytest.raises(ValueError, match=message):
        validate_generation_plan(normalize_canon(_canon()), [row])


def test_plan_binding_must_match_canon_source_key_event_index():
    canon_raw = _canon()
    timeline = canon_raw["timeline"][0]
    timeline.update(
        label="第一日，褚蓝完成零号风钥公开移交",
        source_key_event="第一日，褚蓝完成零号风钥公开移交",
    )
    row = _plan_row(1)
    row.update(
        key_events=["天气晴朗适宜出行", "第一日，褚蓝完成零号风钥公开移交"],
        required_event_ids=["event-weather", "event-transfer"],
        canon_refs=["char-a", "time-1"],
        timeline_event_bindings={"time-1": "event-weather"},
    )

    with pytest.raises(ValueError, match="时间线绑定未对应来源事件"):
        validate_generation_plan(normalize_canon(canon_raw), [row])

    row["timeline_event_bindings"] = {"time-1": "event-transfer"}
    validate_generation_plan(normalize_canon(canon_raw), [row])


def test_gate_two_requires_every_timeline_exactly_once_in_its_source_chapter():
    missing = _plan_row(1)
    missing["canon_refs"] = ["char-a"]
    missing["timeline_event_bindings"] = {}

    with pytest.raises(ValueError, match="必须且只能在来源章节引用"):
        validate_generation_plan(normalize_canon(_canon()), [missing])

    duplicate = _plan_row(1)
    duplicate["canon_refs"].append("time-1")
    with pytest.raises(ValueError, match="必须且只能在来源章节引用"):
        validate_generation_plan(normalize_canon(_canon()), [duplicate])


def test_canon_gate_two_requires_exact_outline_source_but_gate_one_stays_readable():
    missing = _canon()
    missing["timeline"][0].pop("source_key_event")
    with pytest.raises(ValueError, match="缺少大纲事件来源"):
        normalize_canon(missing)

    mismatched = _canon()
    mismatched["timeline"][0]["label"] = "概括标签"
    with pytest.raises(ValueError, match="label 未逐字复制来源事件"):
        normalize_canon(mismatched)

    invented_time = _canon()
    invented_time["timeline"][0]["story_time"] = "第一日 08:00"
    with pytest.raises(ValueError, match="story_time 未逐字来自来源事件"):
        normalize_canon(invented_time)

    legacy = json.loads(json.dumps(_canon(), ensure_ascii=False))
    legacy["gate_version"] = 1
    legacy["timeline"][0].pop("source_chapter_position")
    legacy["timeline"][0].pop("source_key_event")
    assert normalize_canon(legacy, required_gate_version=1)["gate_version"] == 1


def test_timeline_binding_changes_generation_plan_hash():
    plan = {"schema": "story_novel_generation_plan.v2", "chapters": [_timeline_row()]}
    changed = copy.deepcopy(plan)
    changed["chapters"][0]["timeline_event_bindings"]["time-1"] = "event-other"

    assert generation_plan_hash(plan) != generation_plan_hash(changed)


def test_timeline_quote_cannot_borrow_another_current_event():
    body = (
        "2174年8月3日，褚蓝完成零号风钥公开移交并签字确认。"
        "裴衡随后宣布季风窗口将在九月二十日后永久关闭。"
    )
    canon = {
        "timeline": [
            {
                "id": "time-transfer",
                "story_time": "2174年8月3日",
                "immutable": True,
            }
        ]
    }
    chapter = {
        "position": 1,
        "canon_refs": ["time-transfer"],
        "required_event_ids": ["event-transfer", "event-window"],
        "timeline_event_bindings": {"time-transfer": "event-transfer"},
    }
    delta = {
        "occurred_event_ids": ["event-transfer", "event-window"],
        "evidence": {
            "event-transfer": "褚蓝完成零号风钥公开移交并签字确认。",
            "event-window": "裴衡随后宣布季风窗口将在九月二十日后永久关闭。",
        },
        "timeline_evidence": {
            "time-transfer": (
                "2174年8月3日……" "裴衡随后宣布季风窗口将在九月二十日后永久关闭。"
            )
        },
    }

    messages = {
        item["message"]
        for item in timeline_evidence_violations(body, canon, chapter, delta)
    }
    assert "时间线证据未对应绑定事件: time-transfer" in messages

    delta["timeline_evidence"][
        "time-transfer"
    ] = "2174年8月3日……褚蓝完成零号风钥公开移交并签字确认。"
    assert timeline_evidence_violations(body, canon, chapter, delta) == []


def test_timeline_quote_must_equal_the_complete_bound_event_evidence():
    body = (
        "2174年8月3日天气晴朗适宜出行。"
        "褚蓝完成零号风钥公开移交并签字确认。"
        "裴衡宣布季风窗口关闭。"
    )
    canon = {
        "timeline": [
            {
                "id": "time-transfer",
                "story_time": "2174年8月3日",
                "immutable": True,
            }
        ]
    }
    chapter = {
        "position": 1,
        "canon_refs": ["time-transfer"],
        "required_event_ids": ["event-transfer"],
        "timeline_event_bindings": {"time-transfer": "event-transfer"},
    }
    delta = {
        "occurred_event_ids": ["event-transfer"],
        "evidence": {
            "event-transfer": (
                "天气晴朗适宜出行。……褚蓝完成零号风钥公开移交并签字确认。"
            )
        },
        "timeline_evidence": {"time-transfer": "2174年8月3日天气晴朗适宜出行。"},
    }

    assert any(
        item["message"] == "时间线证据未对应绑定事件: time-transfer"
        for item in timeline_evidence_violations(body, canon, chapter, delta)
    )

    delta["evidence"]["event-transfer"] = "褚蓝完成零号风钥公开移交并签字确认。"
    delta["timeline_evidence"]["time-transfer"] = (
        "2174年8月3日天气晴朗适宜出行。" "……褚蓝完成零号风钥公开移交并签字确认。"
    )
    assert any(
        item["message"] == "时间线证据未对应绑定事件: time-transfer"
        for item in timeline_evidence_violations(body, canon, chapter, delta)
    )

    delta["timeline_evidence"]["time-transfer"] = (
        "2174年8月3日……褚蓝完成零号风钥公开移交并签字确认。" "……裴衡宣布季风窗口关闭。"
    )
    assert any(
        item["message"] == "时间线证据未对应绑定事件: time-transfer"
        for item in timeline_evidence_violations(body, canon, chapter, delta)
    )


@pytest.mark.parametrize(
    ("story_time", "qualified_quote"),
    [
        (
            "2174年8月3日 08:00",
            "2174年8月3日08:00……褚蓝完成零号风钥公开移交并签字确认。",
        ),
        (
            "2174年8月3日 傍晚",
            "2174年8月3日傍晚时分……褚蓝完成零号风钥公开移交并签字确认。",
        ),
    ],
)
def test_timeline_evidence_requires_the_canon_time_qualifier(
    story_time, qualified_quote
):
    event_quote = "褚蓝完成零号风钥公开移交并签字确认。"
    chapter = {
        "position": 1,
        "canon_refs": ["time-transfer"],
        "required_event_ids": ["event-transfer"],
        "timeline_event_bindings": {"time-transfer": "event-transfer"},
    }
    canon = {
        "timeline": [
            {
                "id": "time-transfer",
                "story_time": story_time,
                "immutable": True,
            }
        ]
    }
    missing_body = f"2174年8月3日，{event_quote}"
    delta = {
        "occurred_event_ids": ["event-transfer"],
        "evidence": {"event-transfer": event_quote},
        "timeline_evidence": {"time-transfer": f"2174年8月3日……{event_quote}"},
    }

    assert any(
        item["message"] == "时间线证据未对应绑定事件: time-transfer"
        for item in timeline_evidence_violations(missing_body, canon, chapter, delta)
    )

    qualified_body = qualified_quote.replace("……", "，")
    delta["timeline_evidence"]["time-transfer"] = qualified_quote
    assert timeline_evidence_violations(qualified_body, canon, chapter, delta) == []
