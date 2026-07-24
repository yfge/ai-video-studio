import json

from app.services.story.story_novel_evidence_rules import (
    evidence_violations,
    timeline_evidence_violations,
)
from app.services.story.story_novel_state_extraction import _validated_parse

TIMELINE = [
    {
        "id": "time-1",
        "story_time": "2174年8月3日",
        "immutable": True,
    }
]


def _validate(body: str, timeline_quote: str, event_quote: str):
    return _validated_parse(
        json.dumps(
            {
                "occurred_event_ids": ["event-1"],
                "evidence": {"event-1": event_quote},
                "timeline_evidence": {"time-1": timeline_quote},
            },
            ensure_ascii=False,
        ),
        chapter_plan={
            "canon_refs": ["time-1"],
            "required_event_ids": ["event-1"],
            "timeline_event_bindings": {"time-1": "event-1"},
        },
        content_text=body,
        current_timeline=TIMELINE,
    )


def test_real_audit_quotes_are_aligned_without_inventing_source_evidence():
    body = (
        "八月三日的澄砂港，天空是铁灰色的。"
        "黎雁在确认书上签下日期：2174年8月3日。"
        "褚蓝从口袋里掏出一把形状奇特的钥匙。"
        "他将钥匙插入金属盒子的锁孔，掀开盒盖。"
        "零号风钥静静地躺在黑色泡沫内衬里。"
        "“移交完成。”裴衡说，“从此刻起，零号风钥由黎雁路线工程师单独保管。”"
        "经复核，2174年度季风窗口将于九月二十日后永久关闭。"
    )
    payload = {
        "occurred_event_ids": ["event-1-1", "event-1-2"],
        "state_transitions": [
            {
                "subject_id": "zero-wind-key",
                "field": "status",
                "from_value": "未移交",
                "to_value": "已移交",
                "reason": "正文移交",
            }
        ],
        "evidence": {
            "event-1-1": (
                "褚蓝从口袋里掏出一把形状奇特的钥匙"
                "……他将钥匙插入金属盒子的锁孔"
                "……掀开盒盖……零号风钥静静地躺在黑色泡沫内衬里"
                "……移交完成。从此刻起，零号风钥由黎雁路线工程师单独保管。"
            ),
            "event-1-2": "经复核，2174年度季风窗口将于九月二十日后永久关闭。",
        },
        "timeline_evidence": {
            "time-1": (
                "2174年8月3日……褚蓝从口袋里掏出一把形状奇特的钥匙"
                "……他将钥匙插入金属盒子的锁孔"
                "……掀开盒盖……零号风钥静静地躺在黑色泡沫内衬里"
                "……移交完成。从此刻起，零号风钥由黎雁路线工程师单独保管。"
            ),
            "time-2": (
                "2174年8月3日……经复核，2174年度季风窗口将于九月二十日后永久关闭。"
            ),
        },
    }
    timeline = [
        *TIMELINE,
        {
            "id": "time-2",
            "story_time": "2174年8月3日",
            "immutable": True,
        },
    ]

    normalized, error = _validated_parse(
        json.dumps(payload, ensure_ascii=False),
        chapter_plan={
            "canon_refs": ["time-1", "time-2"],
            "required_event_ids": ["event-1-1", "event-1-2"],
            "timeline_event_bindings": {
                "time-1": "event-1-1",
                "time-2": "event-1-2",
            },
        },
        content_text=body,
        current_timeline=timeline,
    )

    assert error is None
    assert normalized["occurred_event_ids"] == payload["occurred_event_ids"]
    assert normalized["state_transitions"] == payload["state_transitions"]
    assert "移交完成……从此刻起" in normalized["evidence"]["event-1-1"]
    assert all(
        "2174年8月3日" in quote for quote in normalized["timeline_evidence"].values()
    )
    assert evidence_violations(body, normalized) == []
    assert (
        timeline_evidence_violations(
            body,
            {"timeline": timeline},
            {
                "canon_refs": ["time-1", "time-2"],
                "required_event_ids": ["event-1-1", "event-1-2"],
                "timeline_event_bindings": {
                    "time-1": "event-1-1",
                    "time-2": "event-1-2",
                },
            },
            normalized,
        )
        == []
    )


def test_timeline_alignment_does_not_move_a_later_date_before_the_event():
    normalized, error = _validate(
        "褚蓝完成风钥移交。档案员随后补写日期：2174年8月3日。",
        "褚蓝完成风钥移交。",
        "褚蓝完成风钥移交。",
    )

    assert normalized is None
    assert "时间线证据缺少固定日期 2174年8月3日: time-1" in error


def test_timeline_audit_can_use_same_event_restatement_after_fixed_date():
    body = (
        "裴衡宣布九月二十日后季风窗口永久关闭。"
        "档案员随后补写日期：2174年8月3日。"
        "裴衡重申，九月二十日不是建议，是截止日期。"
    )

    normalized, error = _validate(
        body,
        "2174年8月3日……九月二十日不是建议，是截止日期。",
        "九月二十日不是建议，是截止日期。",
    )

    assert error is None
    assert normalized is not None
    assert (
        timeline_evidence_violations(
            body,
            {"timeline": TIMELINE},
            {
                "canon_refs": ["time-1"],
                "required_event_ids": ["event-1"],
                "timeline_event_bindings": {"time-1": "event-1"},
            },
            normalized,
        )
        == []
    )


def test_timeline_rejects_date_only_event_then_date_and_unrelated_clause():
    cases = [
        (
            "2174年8月3日，褚蓝完成风钥移交。",
            "2174年8月3日",
            "时间线证据固定日期晚于或缺少对应事件: time-1",
        ),
        (
            "褚蓝完成风钥移交。档案日期：2174年8月3日。",
            "褚蓝完成风钥移交……2174年8月3日",
            "时间线证据固定日期晚于或缺少对应事件: time-1",
        ),
        (
            "2174年8月3日天气晴朗。褚蓝完成风钥移交。",
            "2174年8月3日天气晴朗。",
            "时间线证据未对应绑定事件: time-1",
        ),
    ]
    for body, quote, expected in cases:
        normalized, error = _validate(body, quote, "褚蓝完成风钥移交。")
        assert normalized is None
        assert expected in error


def test_relative_timeline_rejects_empty_evidence():
    normalized, error = _validated_parse(
        json.dumps(
            {
                "occurred_event_ids": ["event-1"],
                "evidence": {"event-1": "褚蓝完成风钥移交。"},
                "timeline_evidence": {"time-1": ""},
            },
            ensure_ascii=False,
        ),
        chapter_plan={
            "canon_refs": ["time-1"],
            "required_event_ids": ["event-1"],
            "timeline_event_bindings": {"time-1": "event-1"},
        },
        content_text="第1日傍晚，褚蓝完成风钥移交。",
        current_timeline=[
            {"id": "time-1", "story_time": "第1日傍晚", "immutable": True}
        ],
    )

    assert normalized is None
    assert "时间线缺少正文证据: time-1" in error


def test_timeline_event_overlap_ignores_shared_dates_and_event_prefixes():
    cases = [
        {
            "body": (
                "2174年8月3日天气晴朗风向稳定适宜出行。随后褚蓝完成风钥移交并签字确认。"
            ),
            "event": "2174年8月3日……褚蓝完成风钥移交并签字确认",
            "timeline": "2174年8月3日……天气晴朗风向稳定适宜出行",
            "message": "时间线证据未对应绑定事件: time-1",
        },
        {
            "body": "风钥移交2174年8月3日天气晴朗。",
            "event": "风钥移交",
            "timeline": "风钥移交2174年8月3日天气晴朗。",
            "message": "时间线证据固定日期晚于或缺少对应事件: time-1",
        },
    ]
    for case in cases:
        normalized, error = _validate(case["body"], case["timeline"], case["event"])
        assert normalized is None
        assert case["message"] in error


def test_timeline_cannot_overlap_an_unclaimed_extra_evidence_key():
    body = "2174年8月3日天气晴朗风向稳定。随后褚蓝完成风钥移交并签字确认。"
    normalized, error = _validated_parse(
        json.dumps(
            {
                "occurred_event_ids": ["event-1"],
                "evidence": {
                    "event-1": "褚蓝完成风钥移交并签字确认。",
                    "junk": "2174年8月3日天气晴朗风向稳定。",
                },
                "timeline_evidence": {"time-1": "2174年8月3日天气晴朗风向稳定。"},
            },
            ensure_ascii=False,
        ),
        chapter_plan={
            "canon_refs": ["time-1"],
            "required_event_ids": ["event-1"],
            "timeline_event_bindings": {"time-1": "event-1"},
        },
        content_text=body,
        current_timeline=TIMELINE,
    )

    assert normalized is None
    assert "正文事件证据必须逐项等于发生事件" in error
    assert "时间线证据未对应绑定事件: time-1" in error
