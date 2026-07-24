import json

import anyio
from app.services.story import story_novel_chapter_gate as chapter_gate
from app.services.story.story_novel_ai_prompts import chapter_gate_repair_prompt
from app.services.story.story_novel_repair_safety import (
    can_reuse_prior_result,
    repair_guidance,
    select_repair_evaluation,
)


def test_prior_body_reuse_is_independent_from_guidance_redaction():
    current_state_error = {
        "code": "state_reversion",
        "message": "状态被回滚: char-a.status",
    }
    future_error = {
        "code": "canon_violation",
        "message": "正文提前完成未来事件: event-future",
    }
    unauthorized_name = {
        "code": "canon_violation",
        "message": "正文引入未授权具名角色: 岑野",
    }
    current_world_rule = {
        "code": "canon_violation",
        "message": "正文违反 Canon 世界规则 rule-6，命中禁项: 海岸",
    }
    length_error = {
        "code": "canon_violation",
        "message": "章节长度为 2999，要求 3000–5000",
    }

    assert can_reuse_prior_result(
        [current_state_error],
        current_event_ids=["event-current"],
        current_timeline_ids=["time-current"],
    )
    assert not can_reuse_prior_result(
        [future_error],
        current_event_ids=["event-current"],
        current_timeline_ids=["time-current"],
    )
    assert not can_reuse_prior_result(
        [length_error, future_error],
        current_event_ids=["event-current"],
        current_timeline_ids=["time-current"],
    )
    assert not can_reuse_prior_result([unauthorized_name])
    assert can_reuse_prior_result([current_world_rule])
    assert not can_reuse_prior_result(
        [
            {
                "code": "canon_violation",
                "message": (
                    "状态提前包含未来里程碑结果: "
                    "第 19 章 mile-r17-confirmed obj-r17.status"
                ),
            }
        ]
    )
    safe_world_guidance = repair_guidance([current_world_rule, unauthorized_name])
    encoded = json.dumps(safe_world_guidance, ensure_ascii=False)
    assert "命中禁项: 海岸" in encoded
    assert "岑野" not in encoded


def test_future_redaction_preserves_current_fixed_date_repair_checklist():
    violations = [
        {
            "code": "canon_violation",
            "message": (
                "章节状态提取失败: 正文提前出现计划第 4 章角色: 岑野；"
                "时间线证据缺少固定日期 2174年8月3日: time-current"
            ),
        }
    ]
    guidance = repair_guidance(
        violations,
        current_event_ids=["event-current"],
        current_timeline_ids=["time-current"],
    )

    prompt = chapter_gate_repair_prompt(
        context_pack={"chapter_contract": {"canon_refs": ["time-current"]}},
        prior_result=None,
        actual_chars=3493,
        target_chars=4000,
        violations=guidance,
    )

    assert "岑野" not in prompt
    assert "第 4 章" not in prompt
    assert "最终固定日期 checklist" in prompt
    assert "2174年8月3日" in prompt


def test_repair_guidance_keeps_only_current_chapter_details():
    safe_messages = [
        "missing JSON object",
        "章节长度为 2999，要求 3000–5000",
        "正文自报本章事件必须逐项等于当前章节合同",
        "正文缺少计划事件: event-current",
        "事件缺少可核对的正文证据: event-current",
        "时间线缺少正文证据: time-current",
        "正文缺少固定日期 2174年8月3日: time-current",
        "正文缺少当前事件固定日期: 九月二十日",
        (
            "章节状态提取失败: 事件缺少可核对的正文证据: event-current；"
            "时间线证据缺少固定日期 2174年8月3日: time-current"
        ),
    ]
    unsafe_messages = [
        "正文提前完成未来事件: future-event-secret",
        "事件缺少可核对的正文证据: future-event-secret",
        "正文提前出现计划第 8 章角色: 未来角色秘名",
        "提前消费里程碑: future-milestone-secret",
        "时间线缺少正文证据: future-time-secret",
        "正文缺少固定日期 2199年12月31日: future-time-secret",
        "未来状态值为 SECRET_FUTURE_VALUE",
        "章节状态提取失败: 事件缺少可核对的正文证据: future-event-secret",
    ]
    guidance = repair_guidance(
        [
            {"code": "canon_violation", "message": message}
            for message in [*safe_messages, *unsafe_messages]
        ],
        current_event_ids=["event-current"],
        current_timeline_ids=["time-current"],
    )
    encoded = json.dumps(guidance, ensure_ascii=False)

    assert all(message in encoded for message in safe_messages)
    for secret in (
        "future-event-secret",
        "未来角色秘名",
        "future-milestone-secret",
        "future-time-secret",
        "2199年12月31日",
        "SECRET_FUTURE_VALUE",
    ):
        assert secret not in encoded
    assert "正文只可完成当前章合同" in encoded
    assert can_reuse_prior_result(
        [
            {"code": "canon_violation", "message": safe_messages[1]},
            {"code": "canon_violation", "message": safe_messages[-1]},
        ],
        current_event_ids=["event-current"],
        current_timeline_ids=["time-current"],
    )
    assert not can_reuse_prior_result(
        [{"code": "canon_violation", "message": unsafe_messages[-1]}],
        current_event_ids=["event-current"],
        current_timeline_ids=["time-current"],
    )


def test_unplanned_location_repair_stays_inside_current_contract():
    guidance = repair_guidance(
        [
            {
                "code": "unexplained_location",
                "message": "正文出现未规划移动: ('char-a', 'loc-a', 'loc-future')",
            }
        ]
    )

    assert guidance == [
        {
            "code": "unexplained_location",
            "message": (
                "只允许当前章 location_transitions 中的地点移动；"
                "清单为空时删除全部移动并保持 current_state 地点"
            ),
        }
    ]


def test_repair_selection_is_strictly_monotonic():
    first = _evaluation("safe", ["missing-date", "missing-event"])
    subset = _evaluation("better", ["missing-date"])
    equal = _evaluation("rewrite", ["missing-date", "missing-event"])
    future = _evaluation("unsafe", ["future-date"])
    passed = {**_evaluation("valid", []), "passed": True}
    missing = {**first, "result": None}

    assert select_repair_evaluation(first, subset) is subset
    assert select_repair_evaluation(first, equal) is first
    assert select_repair_evaluation(first, future) is first
    assert select_repair_evaluation(first, passed) is passed
    assert select_repair_evaluation(missing, future) is future


def test_chapter_gate_keeps_safe_first_body_when_repair_adds_future_date(monkeypatch):
    first = _evaluation("SAFE_FIRST_BODY", ["missing-date"])
    repaired = _evaluation("UNSAFE_FUTURE_DATE", ["future-date"])
    evaluations = iter([first, repaired])

    async def fixed_body(*_args, **_kwargs):
        return "unused"

    async def evaluate(*_args, **_kwargs):
        return next(evaluations)

    monkeypatch.setattr(chapter_gate, "_generate_initial_body", fixed_body)
    monkeypatch.setattr(chapter_gate, "_generate_repaired_body", fixed_body)
    monkeypatch.setattr(chapter_gate, "_evaluate", evaluate)

    async def run():
        return await chapter_gate.generate_validated_chapter(
            object(), chapter_plan={}, context_pack={}, generate_text=None
        )

    result = anyio.run(run)
    assert result["result"]["content_text"] == "SAFE_FIRST_BODY"
    assert not result["passed"]
    assert result["body_repair_count"] == 1


def _evaluation(body: str, messages: list[str]) -> dict:
    return {
        "passed": False,
        "result": {"content_text": body},
        "state_validation": {
            "status": "failed",
            "violations": [
                {"code": "canon_violation", "message": item} for item in messages
            ],
        },
        "state_extraction_evidence_only": False,
        "state_extraction_repair_count": 0,
    }
