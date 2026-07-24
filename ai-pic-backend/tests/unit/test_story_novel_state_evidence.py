import json
from types import SimpleNamespace

from app.services.story.story_novel_evidence_rules import (
    evidence_violations,
    required_event_anchor_violations,
    timeline_evidence_violations,
)
from app.services.story.story_novel_gate_support import premature_plan_violations
from app.services.story.story_novel_state_extraction import _parse, _validated_parse


def test_state_extraction_drops_same_location_noop():
    parsed, error = _parse(
        json.dumps(
            {
                "location_transitions": [
                    {
                        "subject_id": "char-liyan",
                        "from_location_id": "loc-port",
                        "to_location_id": "loc-port",
                        "means": "在港区内步行",
                    }
                ]
            }
        )
    )

    assert error is None
    assert parsed["location_transitions"] == []


def test_evidence_accepts_two_ordered_verbatim_fragments():
    body = (
        "她把玻璃瓶密封好，又从背包里取出一个标有“物证筒”的金属圆筒。"
        "她把样本放进去并拧紧筒盖，然后在筒身的标签上写下编号：R-17。"
    )
    delta = {
        "occurred_event_ids": ["event-r17"],
        "evidence": {
            "event-r17": (
                "她把玻璃瓶密封好，又从背包里取出一个标有'物证筒'的金属圆筒"
                "……在筒身的标签上写下编号：R-17"
            )
        },
    }

    assert evidence_violations(body, delta) == []
    delta["evidence"]["event-r17"] = "她采集了完全不存在的样本"
    assert evidence_violations(body, delta)[0]["message"].endswith("event-r17")


def test_evidence_accepts_multiple_ordered_fragments_from_real_audit():
    body = (
        "褚蓝站在港务局门口的台阶上，然后从身后的保险箱里取出一个金属手提箱。"
        "褚蓝输入密码，打开箱盖，露出里面的内容物——零号风钥。"
    )
    delta = {
        "occurred_event_ids": ["event-transfer"],
        "evidence": {
            "event-transfer": (
                "褚蓝站在港务局门口的台阶上……从身后的保险箱里取出一个金属手提箱"
                "……打开箱盖，露出里面的内容物……零号风钥"
            )
        },
    }

    assert evidence_violations(body, delta) == []


def test_required_event_date_anchor_rejects_neighboring_deadline():
    plan = {"key_events": ["裴衡宣布九月二十日后季风窗口永久关闭"]}
    wrong = "裴衡宣布九月二十一日后季风窗口永久关闭。"
    assert required_event_anchor_violations(wrong, plan) == [
        {
            "code": "canon_violation",
            "message": "正文缺少当前事件固定日期: 九月二十日",
        }
    ]
    correct = "裴衡宣布九月二十日后季风窗口永久关闭。"
    assert required_event_anchor_violations(correct, plan) == []


def test_only_key_event_dates_are_required_before_typed_timeline_audit():
    plan = {
        "key_events": ["1月6日，褚蓝公开移交零号风钥"],
        "end_state": "1月6日傍晚，零号风钥由黎雁保管。",
    }

    assert required_event_anchor_violations("傍晚，移交完成。", plan) == [
        {
            "code": "canon_violation",
            "message": "正文缺少当前事件固定日期: 1月6日",
        }
    ]
    assert required_event_anchor_violations("1月6日，移交完成。", plan) == []


def test_end_state_deadline_is_not_treated_as_chapter_checkpoint():
    plan = {
        "key_events": [],
        "end_state": "8月3日傍晚，零号风钥由黎雁保管，截止九月二十日。",
    }

    assert required_event_anchor_violations("8月3日傍晚，移交完成。", plan) == []


def test_future_unique_date_anchor_is_not_allowed_in_current_body():
    revision = SimpleNamespace(
        generation_plan={
            "canon": {"entities": []},
            "chapters": [
                {"position": 1, "key_events": ["公开移交钥匙"]},
                {"position": 2, "key_events": ["九月二十一日关闭旧站"]},
            ],
        }
    )
    violations = premature_plan_violations(
        revision, 1, "有人断言九月二十一日关闭旧站。"
    )
    assert violations == [
        {
            "code": "canon_violation",
            "message": "正文提前出现计划第 2 章日期: 九月二十一日",
        }
    ]


def test_future_date_gate_matches_arabic_plan_and_chinese_prose():
    revision = SimpleNamespace(
        generation_plan={
            "canon": {"entities": []},
            "chapters": [
                {"position": 1, "key_events": ["公开移交钥匙"]},
                {"position": 48, "key_events": ["9月21日第一场雨抵达六城"]},
            ],
        }
    )

    violations = premature_plan_violations(
        revision, 1, "她被要求在九月二十一日之前完成校准。"
    )

    assert violations == [
        {
            "code": "canon_violation",
            "message": "正文提前出现计划第 48 章日期: 9月21日",
        }
    ]


def test_date_already_disclosed_by_prior_chapter_can_be_reused():
    revision = SimpleNamespace(
        generation_plan={
            "canon": {"entities": []},
            "chapters": [
                {"position": 1, "key_events": ["九月二十日后窗口永久关闭"]},
                {"position": 2, "key_events": ["黎雁检查风钥刻痕"]},
                {"position": 47, "key_events": ["9月20日临时权限到期"]},
            ],
        }
    )

    assert (
        premature_plan_violations(
            revision,
            2,
            "黎雁记得裴衡公开宣布九月二十日后窗口永久关闭。",
        )
        == []
    )


def test_future_date_gate_matches_chinese_year_but_not_a_different_year():
    revision = SimpleNamespace(
        generation_plan={
            "canon": {"entities": []},
            "chapters": [
                {"position": 1, "key_events": ["公开移交钥匙"]},
                {"position": 48, "key_events": ["2174年9月21日第一场雨抵达"]},
            ],
        }
    )

    assert premature_plan_violations(
        revision, 1, "二一七四年九月二十一日将迎来第一场雨。"
    )
    assert (
        premature_plan_violations(revision, 1, "二一七五年九月二十一日将迎来第一场雨。")
        == []
    )


def test_timeline_evidence_requires_current_fixed_date():
    canon = {
        "timeline": [
            {
                "id": "time-1",
                "story_time": "2174年8月3日",
                "immutable": True,
            }
        ]
    }
    plan = {
        "canon_refs": ["time-1"],
        "required_event_ids": ["event-1"],
        "timeline_event_bindings": {"time-1": "event-1"},
    }
    body = "2174年8月3日，褚蓝在公开见证下交出零号风钥。"
    delta = {
        "occurred_event_ids": ["event-1"],
        "evidence": {"event-1": "褚蓝在公开见证下交出零号风钥。"},
        "timeline_evidence": {"time-1": body},
    }

    assert timeline_evidence_violations(body, canon, plan, delta) == []
    wrong_date = body.replace("8月3日", "8月4日")
    violations = timeline_evidence_violations(wrong_date, canon, plan, delta)
    assert {item["message"] for item in violations} == {
        "时间线缺少正文证据: time-1",
        "正文缺少固定日期 2174年8月3日: time-1",
    }


def test_state_audit_repairs_short_fragmented_timeline_evidence():
    body = (
        "2174年8月3日08:00，褚蓝在公开见证下完成风钥移交。"
        "2174年8月3日傍晚时分，裴衡宣布季风窗口将在九月二十日后永久关闭。"
    )
    timeline = [
        {
            "id": "time-1",
            "story_time": "2174年8月3日 08:00",
            "immutable": True,
        },
        {
            "id": "time-2",
            "story_time": "2174年8月3日 傍晚",
            "immutable": True,
        },
    ]
    payload = {
        "occurred_event_ids": ["event-1", "event-2"],
        "evidence": {
            "event-1": "褚蓝在公开见证下完成风钥移交。",
            "event-2": "裴衡宣布季风窗口将在九月二十日后永久关闭。",
        },
        "timeline_evidence": {
            "time-1": "2174年8月3日08:00，褚蓝在公开见证下完成风钥移交。",
            "time-2": "八月三日……傍晚时分",
        },
    }

    normalized, error = _validated_parse(
        json.dumps(payload, ensure_ascii=False),
        chapter_plan={
            "canon_refs": ["time-1", "time-2"],
            "required_event_ids": ["event-1", "event-2"],
            "timeline_event_bindings": {
                "time-1": "event-1",
                "time-2": "event-2",
            },
        },
        content_text=body,
        current_timeline=timeline,
    )

    assert normalized is None
    assert error == (
        "时间线缺少正文证据: time-2；时间线证据未对应绑定事件: time-2；"
        "时间线证据缺少固定日期 2174年8月3日: time-2"
    )
    payload["timeline_evidence"][
        "time-2"
    ] = "2174年8月3日傍晚时分，裴衡宣布季风窗口将在九月二十日后永久关闭。"
    normalized, error = _validated_parse(
        json.dumps(payload, ensure_ascii=False),
        chapter_plan={
            "canon_refs": ["time-1", "time-2"],
            "required_event_ids": ["event-1", "event-2"],
            "timeline_event_bindings": {
                "time-1": "event-1",
                "time-2": "event-2",
            },
        },
        content_text=body,
        current_timeline=timeline,
    )
    assert error is None
    assert normalized["timeline_evidence"] == payload["timeline_evidence"]
