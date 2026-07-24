import json

import anyio
from app.services.story.story_novel_chapter_service import generate_or_resume_chapter
from tests.unit.test_story_novel_canon_state import _body, _delta, _v2_revision
from tests.unit.test_story_novel_longform import _plan_row, _setup


def test_invalid_audit_evidence_repairs_extraction_without_body_rewrite(
    db_session, monkeypatch
):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    current = _plan_row(1)
    _v2_revision(revision, current)
    db_session.commit()
    prompts = []
    audit_calls = 0

    async def generate(_revision, prompt, **_kwargs):
        nonlocal audit_calls
        prompts.append(prompt)
        if "从实际小说正文提取" not in prompt:
            payload = json.loads(_body_with_current_timeline())
            payload["content_text"] = (
                "SAFE_CURRENT_DRAFT_MARKER" + payload["content_text"]
            )
            return json.dumps(payload, ensure_ascii=False)
        audit_calls += 1
        if audit_calls == 1:
            delta = json.loads(_delta_with_current_timeline())
            delta["evidence"]["event-1"] = "CURRENT_EVENT_EVIDENCE_MISSING"
            return json.dumps(delta, ensure_ascii=False)
        delta = json.loads(_delta_with_current_timeline())
        return json.dumps(
            {
                "evidence": delta["evidence"],
                "timeline_evidence": delta.get("timeline_evidence", {}),
            },
            ensure_ascii=False,
        )

    async def extracted(*_args, **_kwargs):
        return {"events": [], "memories": []}

    monkeypatch.setattr(
        "app.services.story.story_novel_candidate_checkpoint."
        "NarrativeExtractionService.extract",
        extracted,
    )
    monkeypatch.setattr(
        "app.services.story.story_novel_candidate_checkpoint."
        "complete_novel_candidate_set",
        lambda *_args: True,
    )
    anyio.run(generate_or_resume_chapter, service, revision, task, current, generate)
    prose_prompts = [item for item in prompts if "从实际小说正文提取" not in item]
    repair_prompt = [item for item in prompts if "上一次状态提取无效" in item][0]
    assert len(prose_prompts) == 1
    assert audit_calls == 2
    assert "SAFE_CURRENT_DRAFT_MARKER" in repair_prompt
    assert "事件缺少可核对的正文证据: event-1" in repair_prompt
    assert "typed state 已冻结" in repair_prompt
    assert "不得修改任何事件 ID 或状态" in repair_prompt
    assert "上一版章节未通过长篇硬门禁" not in repair_prompt


def test_future_audit_values_are_redacted_from_body_repair(db_session, monkeypatch):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    current = _plan_row(1)
    future = {
        **_plan_row(2),
        "title": "FUTURE_CHAPTER_TITLE",
        "goal": "FUTURE_EVENT_SECRET",
        "key_events": ["FUTURE_EVENT_SECRET"],
        "required_event_ids": ["future-death-event-2"],
    }
    _v2_revision(revision, current)
    revision.generation_plan = {
        **dict(revision.generation_plan),
        "chapter_count": 2,
        "target_chars": 6000,
        "chapters": [current, future],
    }
    revision.chapter_count = 2
    db_session.commit()
    prompts = []
    audit_calls = 0

    async def generate(_revision, prompt, **_kwargs):
        nonlocal audit_calls
        prompts.append(prompt)
        if "从实际小说正文提取" not in prompt:
            payload = json.loads(_body_with_current_timeline())
            payload["content_text"] = (
                "UNTRUSTED_FIRST_DRAFT_SECRET" + payload["content_text"]
            )
            return json.dumps(payload, ensure_ascii=False)
        audit_calls += 1
        if audit_calls == 1:
            delta = json.loads(
                _delta_with_current_timeline(
                    premature=["future-death-event-2"],
                    future_event_id="future-death-event-2",
                )
            )
            delta["evidence"]["event-1"] = "CURRENT_EVENT_EVIDENCE_MISSING"
            return json.dumps(delta, ensure_ascii=False)
        return _delta_with_current_timeline(future_event_id="future-death-event-2")

    async def extracted(*_args, **_kwargs):
        return {"events": [], "memories": []}

    monkeypatch.setattr(
        "app.services.story.story_novel_candidate_checkpoint."
        "NarrativeExtractionService.extract",
        extracted,
    )
    monkeypatch.setattr(
        "app.services.story.story_novel_candidate_checkpoint."
        "complete_novel_candidate_set",
        lambda *_args: True,
    )
    anyio.run(
        generate_or_resume_chapter,
        service,
        revision,
        task,
        current,
        generate,
    )
    prose_prompts = [item for item in prompts if "从实际小说正文提取" not in item]
    audit_prompts = [item for item in prompts if "从实际小说正文提取" in item]
    assert len(prose_prompts) == 1
    assert len(audit_prompts) == 2
    assert "上一次状态提取无效" in audit_prompts[1]
    for prompt in prose_prompts:
        assert "future-death-event-2" not in prompt
        assert "FUTURE_EVENT_SECRET" not in prompt
        assert "FUTURE_CHAPTER_TITLE" not in prompt
    assert "事件缺少可核对的正文证据: event-1" in audit_prompts[1]
    assert "UNTRUSTED_FIRST_DRAFT_SECRET" in audit_prompts[1]


def test_semantic_future_violation_discards_prior_and_redacts_body_repair(
    db_session, monkeypatch
):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    current = _plan_row(1)
    future = {
        **_plan_row(2),
        "title": "FUTURE_R17_CHAPTER",
        "goal": "完成R-17来源化验",
        "key_events": ["银脊化验确认R-17来自人工增旱阀仓"],
        "required_event_ids": ["event-r17-confirmed"],
    }
    _v2_revision(revision, current)
    revision.generation_plan = {
        **dict(revision.generation_plan),
        "chapter_count": 2,
        "target_chars": 6000,
        "chapters": [current, future],
    }
    revision.chapter_count = 2
    db_session.commit()
    prompts = []
    body_calls = 0

    async def generate(_revision, prompt, **_kwargs):
        nonlocal body_calls
        prompts.append(prompt)
        if "从实际小说正文提取" in prompt:
            return _delta_with_current_timeline(future_event_id="event-r17-confirmed")
        body_calls += 1
        if body_calls == 1:
            payload = json.loads(_body_with_current_timeline())
            payload["content_text"] = (
                "UNTRUSTED_FUTURE_DRAFT。管壁附着增旱阀仓沉积物。"
                "黎雁断定R-17只可能来自人为投放。" + payload["content_text"]
            )
            return json.dumps(payload, ensure_ascii=False)
        return _body_with_current_timeline()

    async def extracted(*_args, **_kwargs):
        return {"events": [], "memories": []}

    monkeypatch.setattr(
        "app.services.story.story_novel_candidate_checkpoint."
        "NarrativeExtractionService.extract",
        extracted,
    )
    monkeypatch.setattr(
        "app.services.story.story_novel_candidate_checkpoint."
        "complete_novel_candidate_set",
        lambda *_args: True,
    )
    anyio.run(
        generate_or_resume_chapter,
        service,
        revision,
        task,
        current,
        generate,
    )

    prose_prompts = [item for item in prompts if "从实际小说正文提取" not in item]
    assert len(prose_prompts) == 2
    assert "上一版正文、摘要、卡点和自报状态含不可披露问题" in prose_prompts[1]
    assert "UNTRUSTED_FUTURE_DRAFT" not in prose_prompts[1]
    for prompt in prose_prompts:
        assert "event-r17-confirmed" not in prompt
        assert "银脊化验确认R-17来自人工增旱阀仓" not in prompt
        assert "FUTURE_R17_CHAPTER" not in prompt


def _body_with_current_timeline() -> str:
    payload = json.loads(_body())
    payload["content_text"] = "第一日，" + payload["content_text"]
    return json.dumps(payload, ensure_ascii=False)


def _delta_with_current_timeline(
    *,
    premature: list[str] | None = None,
    future_event_id: str | None = None,
) -> str:
    payload = json.loads(_delta(premature=premature))
    event_quote = payload["evidence"]["event-1"]
    if future_event_id:
        payload["future_event_audit"] = {
            future_event_id: (
                "premature" if future_event_id in (premature or []) else "not_present"
            )
        }
    payload["timeline_evidence"] = {"time-1": f"第一日，{event_quote}"}
    return json.dumps(payload, ensure_ascii=False)
