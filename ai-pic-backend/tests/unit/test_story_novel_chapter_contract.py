import json

import anyio
from app.services.story.story_novel_ai_prompts import (
    chapter_gate_repair_prompt,
    chapter_length_repair_prompt,
    chapter_prompt,
)
from app.services.story.story_novel_chapter_service import (
    _parse_chapter,
    generate_or_resume_chapter,
    non_whitespace_chars,
)
from tests.unit.test_story_novel_longform import _plan_row, _setup


def test_chapter_length_repairs_once_and_checkpoints(db_session, monkeypatch):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    row = _plan_row()
    revision.generation_plan = {
        "status": "ready",
        "chapter_count": 1,
        "target_chars": 3000,
        "chapters": [row],
    }
    revision.chapter_count = 1
    calls = 0

    async def generate(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        content = "短" * 100 if calls == 1 else "长" * 3000
        return json.dumps(
            {
                "title": "第一章",
                "content_text": content,
                "summary": "摘要",
                "plot_delta": {"unresolved_threads": ["裂缝来源"]},
            },
            ensure_ascii=False,
        )

    async def extracted(*_args, **_kwargs):
        return {"events": [], "memories": []}

    monkeypatch.setattr(
        "app.services.story.story_novel_chapter_service.NarrativeExtractionService.extract",
        extracted,
    )
    chapter = anyio.run(
        generate_or_resume_chapter, service, revision, task, row, generate
    )
    assert calls == 2
    assert non_whitespace_chars(chapter.content_text) == 3000
    assert revision.continuity_ledger["chapters"]["1"]["extraction_status"] == "ready"


def test_length_repair_prompt_does_not_echo_entire_oversized_body():
    oversized = "正文" * 3000
    prompt = chapter_length_repair_prompt(
        context_pack={"chapter_plan": _plan_row()},
        prior_result={
            "title": "第一章",
            "content_text": oversized,
            "summary": "发现裂缝",
            "cliffhanger": "门后有声音",
            "plot_delta": {"key_events": ["发现线索"]},
        },
        actual_chars=len(oversized),
        target_chars=4200,
    )
    assert oversized not in prompt
    assert oversized[:300] in prompt
    assert "绝对不要超过 4000" in prompt


def test_chapter_parser_accepts_common_body_alias():
    parsed, error = _parse_chapter(
        json.dumps(
            {
                "title": "第一章",
                "body": "正文" * 1500,
                "summary": "发现裂缝",
                "plot_delta": {},
            },
            ensure_ascii=False,
        )
    )
    assert error is None
    assert parsed["content_text"] == "正文" * 1500


def test_gate_repair_locks_current_event_fixed_date():
    prompt = chapter_gate_repair_prompt(
        context_pack={"chapter_contract": _plan_row()},
        prior_result={"content_text": "安全首稿"},
        actual_chars=3989,
        target_chars=4000,
        violations=[
            {
                "code": "canon_violation",
                "message": "正文缺少当前事件固定日期: 九月二十日",
            },
            {
                "code": "canon_violation",
                "message": ("章节状态提取失败: 正文缺少固定日期 2174年8月3日: time-1"),
            },
        ],
    )
    assert "最终固定日期 checklist" in prompt
    assert '["九月二十日","2174年8月3日"]' in prompt
    assert "正文首段第一句先写 checklist 中最早日期" in prompt
    assert "事后补写不算" in prompt
    assert "不得用相邻日期、次日或 Story 全局结束日替代" in prompt
    assert prompt.index("上一版完整正文") < prompt.index("最终固定日期 checklist")


def test_chapter_prompt_forbids_deriving_an_adjacent_future_date():
    prompt = chapter_prompt(
        context_pack={"chapter_contract": _plan_row()},
        target_chars=4000,
    )

    assert "不得新增当前 chapter_contract" in prompt
    assert "“某日后”只能原样写“某日后”" in prompt
    assert "绝不能换算成次日或其他相邻日期" in prompt
    assert "不得为它补写修改时间、人物身份、原因、答案、未来权限或后果" in prompt
    assert "不得把它写入 resolved_threads" in prompt
    assert "location_transitions 是本章允许发生的全部地点移动" in prompt
    assert "“准备转移”不等于出发、登船、起锚或抵达" in prompt


def test_gate_repair_compensates_for_large_underproduction():
    prompt = chapter_gate_repair_prompt(
        context_pack={"chapter_contract": _plan_row()},
        prior_result={"content_text": "安全首稿"},
        actual_chars=2672,
        target_chars=4000,
        violations=[],
    )

    assert "安全目标约 4600" in prompt
    assert "净增至少 728 个非空白字符" in prompt
    assert "不得为它补写修改时间、人物身份、原因、答案、未来权限或后果" in prompt
