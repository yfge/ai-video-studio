import anyio
import pytest
from app.services.story.story_novel_canon_service import normalize_canon
from app.services.story.story_novel_chapter_service import generate_or_resume_chapter
from app.services.story.story_novel_state_service import initial_story_state
from app.services.story.story_novel_state_validator import validate_state_delta
from fastapi import HTTPException
from tests.unit.test_story_novel_canon_state import _body, _delta, _v2_revision
from tests.unit.test_story_novel_longform import _canon, _plan_row, _setup


def test_gate_failed_prefix_blocks_later_chapter_generation(db_session, monkeypatch):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    first = _plan_row(1)
    second = {**_plan_row(2), "required_event_ids": ["event-2"]}
    _v2_revision(revision, first)
    revision.generation_plan = {
        **dict(revision.generation_plan),
        "chapter_count": 2,
        "target_chars": 6000,
        "chapters": [first, second],
    }
    revision.chapter_count = 2
    db_session.commit()

    async def fail_first(_revision, prompt, **_kwargs):
        return (
            _delta(world_rule_violations=["rule-violation"])
            if "从实际小说正文提取" in prompt
            else _body()
        )

    async def must_not_extract(*_args, **_kwargs):
        raise AssertionError("Narrative extraction must wait for the hard gate")

    monkeypatch.setattr(
        "app.services.story.story_novel_chapter_service.NarrativeExtractionService.extract",
        must_not_extract,
    )
    with pytest.raises(HTTPException) as exc:
        anyio.run(
            generate_or_resume_chapter,
            service,
            revision,
            task,
            first,
            fail_first,
        )
    assert "Canon/状态门禁失败" in str(exc.value.detail)

    later_calls = 0

    async def must_not_generate(*_args, **_kwargs):
        nonlocal later_calls
        later_calls += 1
        return _body()

    with pytest.raises(HTTPException) as exc:
        anyio.run(
            generate_or_resume_chapter,
            service,
            revision,
            task,
            second,
            must_not_generate,
        )
    assert "第 1 章正文或来源 hash 前缀不完整" in str(exc.value.detail)
    assert later_calls == 0
    assert "current_state" not in revision.continuity_ledger


def test_state_gate_rejects_premature_future_event():
    canon = normalize_canon(_canon())
    row = _plan_row(1)
    delta = {
        "occurred_event_ids": ["event-1"],
        "premature_future_event_ids": ["event-2"],
        "state_transitions": [],
        "knowledge_grants": [],
        "location_transitions": [],
        "milestones_consumed": [],
        "opened_thread_ids": [],
        "resolved_thread_ids": [],
        "world_rule_violations": [],
    }
    report, _state_after = validate_state_delta(
        canon, row, initial_story_state(canon), delta
    )
    assert report["status"] == "failed"
    assert any(
        item["message"] == "正文提前完成未来事件: event-2"
        for item in report["violations"]
    )
