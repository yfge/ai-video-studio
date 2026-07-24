import json

import anyio
import pytest
from app.services.story.story_novel_canon_service import normalize_canon
from app.services.story.story_novel_chapter_service import generate_or_resume_chapter
from app.services.story.story_novel_state_service import (
    initial_story_state,
    quality_metrics,
    state_hash,
)
from fastapi import HTTPException
from tests.unit.test_story_novel_canon_state import _body, _delta, _v2_revision
from tests.unit.test_story_novel_longform import _canon, _plan_row, _setup

_DRYLAND_RULE = {
    "id": "rule-6",
    "statement": (
        "旱海六城是内陆干旱文明；澄砂港的“港”指陆路货运沙港，"
        "不临天然海洋，不存在海岸、海船、渔业或海水景观。"
    ),
    "exceptions": [],
}


def _install_dryland_canon(revision):
    raw = _canon()
    raw["world_rules"] = [_DRYLAND_RULE]
    canon = normalize_canon(raw)
    revision.generation_plan = dict(
        revision.generation_plan, canon=canon, canon_hash=canon["canon_hash"]
    )


def _coastal_body():
    payload = json.loads(_body())
    payload["content_text"] = "车队驶过东海岸。" + payload["content_text"]
    return json.dumps(payload, ensure_ascii=False)


def _allow_empty_candidates(monkeypatch):
    monkeypatch.setattr(
        "app.services.story.story_novel_candidate_checkpoint."
        "complete_novel_candidate_set",
        lambda *_args: True,
    )


def test_v2_chapter_passes_state_gate_then_extracts_memory(db_session, monkeypatch):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    row = _plan_row()
    canon = _v2_revision(revision, row)
    db_session.commit()
    calls = []

    async def generate(_revision, prompt, **_kwargs):
        calls.append(prompt)
        return _delta() if "从实际小说正文提取" in prompt else _body()

    async def extracted(*_args, **_kwargs):
        return {"events": [], "memories": []}

    monkeypatch.setattr(
        "app.services.story.story_novel_chapter_service.NarrativeExtractionService.extract",
        extracted,
    )
    _allow_empty_candidates(monkeypatch)
    chapter = anyio.run(
        generate_or_resume_chapter, service, revision, task, row, generate
    )
    entry = revision.continuity_ledger["chapters"]["1"]
    assert chapter.review_status == "ready"
    assert entry["status"] == "ready"
    assert entry["state_validation"]["status"] == "passed"
    assert entry["canon_hash"] == canon["canon_hash"]
    assert entry["state_before_hash"] == state_hash(initial_story_state(canon))
    assert entry["extraction_status"] == "ready"
    assert len(calls) == 2


def test_prose_canon_failure_repairs_before_typed_audit(db_session, monkeypatch):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    row = _plan_row()
    _v2_revision(revision, row)
    _install_dryland_canon(revision)
    db_session.commit()
    calls = []
    narrative_calls = 0

    async def generate(_revision, prompt, **_kwargs):
        if "从实际小说正文提取" in prompt:
            calls.append("audit")
            return _delta()
        calls.append("body")
        return _coastal_body() if calls.count("body") == 1 else _body()

    async def extracted(*_args, **_kwargs):
        nonlocal narrative_calls
        narrative_calls += 1
        return {"events": [], "memories": []}

    monkeypatch.setattr(
        "app.services.story.story_novel_chapter_service.NarrativeExtractionService.extract",
        extracted,
    )
    _allow_empty_candidates(monkeypatch)
    chapter = anyio.run(
        generate_or_resume_chapter, service, revision, task, row, generate
    )

    entry = revision.continuity_ledger["chapters"]["1"]
    assert calls == ["body", "body", "audit"]
    assert narrative_calls == 1
    assert "东海岸" not in chapter.content_text
    assert entry["body_repair_count"] == 1
    assert entry["state_validation"]["status"] == "passed"
    assert entry["status"] == "ready"


def test_repeated_prose_canon_failure(db_session, monkeypatch):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    row = _plan_row()
    _v2_revision(revision, row)
    _install_dryland_canon(revision)
    db_session.commit()
    body_calls = 0
    audit_calls = 0
    narrative_calls = 0

    async def generate(_revision, prompt, **_kwargs):
        nonlocal body_calls, audit_calls
        if "从实际小说正文提取" in prompt:
            audit_calls += 1
            return _delta()
        body_calls += 1
        return _coastal_body()

    async def extracted(*_args, **_kwargs):
        nonlocal narrative_calls
        narrative_calls += 1
        return {"events": [], "memories": []}

    monkeypatch.setattr(
        "app.services.story.story_novel_chapter_service.NarrativeExtractionService.extract",
        extracted,
    )
    with pytest.raises(HTTPException, match="Canon/状态门禁失败"):
        anyio.run(generate_or_resume_chapter, service, revision, task, row, generate)

    entry = revision.continuity_ledger["chapters"]["1"]
    assert [body_calls, audit_calls, narrative_calls] == [2, 0, 0]
    assert entry["body_repair_count"] == 1
    assert (entry["status"], entry["extraction_status"]) == ("gate_failed", "blocked")
    assert "current_state" not in revision.continuity_ledger


def test_v2_ignores_prose_self_report_and_promotes_typed_plot(db_session, monkeypatch):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    row = _plan_row()
    _v2_revision(revision, row)
    db_session.commit()
    body = json.loads(_body())
    body["plot_delta"] = {
        "key_events": ["模型自报的未来事件"],
        "unresolved_threads": ["模型自报的未来伏笔"],
        "resolved_threads": ["模型自报的未来回收"],
        "character_states": {"char-a": {"knowledge": ["未来真相"]}},
    }

    async def generate(_revision, prompt, **_kwargs):
        return _delta() if "从实际小说正文提取" in prompt else json.dumps(body)

    async def extracted(*_args, **_kwargs):
        return {"events": [], "memories": []}

    monkeypatch.setattr(
        "app.services.story.story_novel_chapter_service.NarrativeExtractionService.extract",
        extracted,
    )
    _allow_empty_candidates(monkeypatch)
    anyio.run(generate_or_resume_chapter, service, revision, task, row, generate)

    entry = revision.continuity_ledger["chapters"]["1"]
    assert entry["status"] == "ready"
    assert entry["plot_delta_source"] == "typed_state"
    assert entry["plot_delta"] == {
        "key_events": ["第一日，发现线索"],
        "unresolved_threads": [],
        "resolved_threads": [],
        "character_states": {},
    }


def test_v2_gate_failure_checkpoints_body_without_advancing_state(
    db_session, monkeypatch
):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    row = _plan_row()
    _v2_revision(revision, row)
    db_session.commit()
    body_calls = 0

    async def generate(_revision, prompt, **_kwargs):
        nonlocal body_calls
        if "从实际小说正文提取" in prompt:
            return _delta(world_rule_violations=["rule-violation"])
        body_calls += 1
        return _body()

    async def must_not_extract(*_args, **_kwargs):
        raise AssertionError("Narrative extraction must wait for the hard gate")

    monkeypatch.setattr(
        "app.services.story.story_novel_chapter_service.NarrativeExtractionService.extract",
        must_not_extract,
    )
    with pytest.raises(HTTPException) as exc:
        anyio.run(generate_or_resume_chapter, service, revision, task, row, generate)
    assert "Canon/状态门禁失败" in str(exc.value.detail)
    entry = revision.continuity_ledger["chapters"]["1"]
    assert body_calls == 2
    assert revision.chapters[0].review_status == "review_required"
    assert entry["status"] == "gate_failed"
    assert entry["body_repair_count"] == 1
    assert entry["state_delta"] is None
    assert entry["state_after"] is None
    assert entry["plot_delta"] is None
    assert entry["gate_evidence"]["candidate_state_delta"] is not None
    assert "current_state" not in revision.continuity_ledger
    assert quality_metrics(revision)["canon_violation_count"] > 0
