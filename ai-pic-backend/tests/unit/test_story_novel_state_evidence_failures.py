import json

import anyio
import pytest
from app.services.story.story_novel_chapter_service import generate_or_resume_chapter
from app.services.story.story_novel_state_extraction import (
    StateExtractionError,
    extract_chapter_state,
)
from fastapi import HTTPException
from tests.unit.test_story_novel_canon_state import _v2_revision
from tests.unit.test_story_novel_longform import _plan_row, _setup
from tests.unit.test_story_novel_state_extraction_repair import _audit_payload


def test_identical_invalid_evidence_repair_stays_fail_closed():
    exact_quote = (
        "“我，褚蓝，澄砂港路线调度员，现依水议会第417号决议，"
        "将零号风钥移交予旱海路线工程师黎雁。”"
    )
    invalid_quote = f"褚蓝双手捧着金属盒，递到黎雁面前……{exact_quote}"
    invalid = _audit_payload(
        f"2174年8月3日……{invalid_quote}",
        invalid_quote,
    )
    calls = 0

    async def generate(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        return invalid

    async def run():
        return await extract_chapter_state(
            object(),
            chapter_plan={
                "canon_refs": ["time-1"],
                "required_event_ids": ["event-1"],
                "timeline_event_bindings": {"time-1": "event-1"},
            },
            state_before={},
            content_text=f"2174年8月3日，交接开始。{exact_quote}",
            future_event_catalog=[],
            current_timeline=[
                {
                    "id": "time-1",
                    "story_time": "2174年8月3日",
                    "immutable": True,
                }
            ],
            generate_text=generate,
        )

    with pytest.raises(StateExtractionError, match="只能返回 evidence") as caught:
        anyio.run(run)

    assert calls == 2
    assert caught.value.repair_count == 1
    assert caught.value.evidence_only is True


def test_failed_evidence_audit_is_blocked_without_rewriting_body(
    db_session, monkeypatch
):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    row = _plan_row()
    _v2_revision(revision, row)
    db_session.commit()
    body = json.dumps(
        {
            "title": "第一章",
            "content_text": "SAFE_BODY_MARKER主角在城门发现裂缝。"
            + "守门记录仍然完整。" * 360,
            "summary": "主角发现裂缝",
            "plot_delta": {},
        },
        ensure_ascii=False,
    )
    body_calls = 0
    audit_calls = 0
    body_temperatures = []
    audit_temperatures = []

    async def generate(_revision, prompt, **_kwargs):
        nonlocal body_calls, audit_calls
        if "从实际小说正文提取" not in prompt:
            body_calls += 1
            body_temperatures.append(_kwargs.get("temperature"))
            return body
        audit_calls += 1
        audit_temperatures.append(_kwargs.get("temperature"))
        invalid = json.loads(_audit_payload(""))
        invalid["evidence"]["event-1"] = "正文中不存在的事件证据"
        return json.dumps(invalid, ensure_ascii=False)

    async def extracted(*_args, **_kwargs):
        raise AssertionError("Narrative extraction must wait for state validation")

    monkeypatch.setattr(
        "app.services.story.story_novel_candidate_checkpoint."
        "NarrativeExtractionService.extract",
        extracted,
    )
    with pytest.raises(HTTPException, match="状态提取待恢复"):
        anyio.run(generate_or_resume_chapter, service, revision, task, row, generate)

    entry = revision.continuity_ledger["chapters"]["1"]
    assert body_calls == 1
    assert audit_calls == 2
    assert body_temperatures == [None]
    assert audit_temperatures == [0.0, 0.0]
    assert entry["body_repair_count"] == 0
    assert entry["state_extraction_repair_count"] == 1
    assert entry["status"] == "state_pending"
    assert entry["state_pending_reason"] == "source_evidence"
    assert entry["extraction_status"] == "blocked"
    assert entry["state_delta"] is None
    assert "current_state" not in revision.continuity_ledger
