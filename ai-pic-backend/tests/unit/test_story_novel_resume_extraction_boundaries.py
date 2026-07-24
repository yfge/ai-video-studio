import json

import anyio
import pytest
from app.core.exceptions import ConflictError
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.services.narrative_memory.extraction_service import NarrativeExtractionService
from app.services.narrative_memory.source_hash import novel_chapter_source_hash
from app.services.story.story_novel_chapter_service import generate_or_resume_chapter
from app.services.story.story_novel_domain import sha256_text
from app.services.story.story_novel_state_service import initial_story_state, state_hash
from tests.unit.test_story_novel_canon_state import _body, _delta, _v2_revision
from tests.unit.test_story_novel_chapter_state_gate import (
    _coastal_body,
    _install_dryland_canon,
)
from tests.unit.test_story_novel_longform import _plan_row, _setup


async def _empty_extraction(*_args, **_kwargs):
    return {"events": [], "memories": []}


def _allow_empty_candidate_set(monkeypatch):
    monkeypatch.setattr(
        "app.services.story.story_novel_candidate_checkpoint."
        "complete_novel_candidate_set",
        lambda *_args: True,
    )


def test_v2_resume_replays_typed_delta_before_reusing_body(db_session, monkeypatch):
    _allow_empty_candidate_set(monkeypatch)
    _user, _story, service, revision, task, *_ = _setup(db_session)
    row = _plan_row()
    canon = _v2_revision(revision, row)
    db_session.commit()
    monkeypatch.setattr(
        "app.services.story.story_novel_chapter_service."
        "NarrativeExtractionService.extract",
        _empty_extraction,
    )

    async def initial(_revision, prompt, **_kwargs):
        return _delta() if "从实际小说正文提取" in prompt else _body()

    anyio.run(generate_or_resume_chapter, service, revision, task, row, initial)
    ledger = dict(revision.continuity_ledger)
    entries = dict(ledger["chapters"])
    entry = dict(entries["1"])
    inconsistent_after = initial_story_state(canon)
    entry["state_after"] = inconsistent_after
    entry["state_after_hash"] = state_hash(inconsistent_after)
    entries["1"] = entry
    ledger["chapters"] = entries
    ledger["current_state"] = inconsistent_after
    revision.continuity_ledger = ledger
    db_session.commit()
    body_calls = 0

    async def regenerate(_revision, prompt, **_kwargs):
        nonlocal body_calls
        if "从实际小说正文提取" in prompt:
            return _delta()
        body_calls += 1
        return _body()

    anyio.run(generate_or_resume_chapter, service, revision, task, row, regenerate)

    assert body_calls == 1
    repaired = revision.continuity_ledger["chapters"]["1"]
    assert repaired["status"] == "ready"
    assert repaired["state_after"] != inconsistent_after
    assert repaired["state_after_hash"] == state_hash(repaired["state_after"])


@pytest.mark.parametrize("checkpoint_status", ["body_ready", "ready"])
def test_resume_rechecks_pending_body(db_session, monkeypatch, checkpoint_status):
    _allow_empty_candidate_set(monkeypatch)
    _user, _story, service, revision, task, *_ = _setup(db_session)
    row = _plan_row()
    _v2_revision(revision, row)
    _install_dryland_canon(revision)
    db_session.commit()
    monkeypatch.setattr(
        "app.services.story.story_novel_chapter_service."
        "NarrativeExtractionService.extract",
        _empty_extraction,
    )

    async def initial(_revision, prompt, **_kwargs):
        return _delta() if "从实际小说正文提取" in prompt else _body()

    chapter = anyio.run(
        generate_or_resume_chapter, service, revision, task, row, initial
    )
    chapter.content_text = json.loads(_coastal_body())["content_text"]
    chapter.content_hash = sha256_text(chapter.content_text)
    invalid_body_hash = chapter.content_hash
    ledger = dict(revision.continuity_ledger)
    entry = dict(ledger["chapters"]["1"])
    entry.update(
        {
            "status": checkpoint_status,
            "body_hash": invalid_body_hash,
            "source_hash": novel_chapter_source_hash(chapter),
            "char_count": len("".join(chapter.content_text.split())),
            "extraction_status": "pending",
            "event_ids": [],
            "memory_ids": [],
        }
    )
    ledger["chapters"] = {"1": entry}
    if checkpoint_status == "body_ready":
        ledger.pop("current_state", None)
    revision.continuity_ledger = ledger
    db_session.commit()
    calls = []

    async def regenerate(_revision, prompt, **_kwargs):
        if "从实际小说正文提取" in prompt:
            calls.append("audit")
            return _delta()
        calls.append("body")
        return _body()

    async def extract_rewritten(*_args, **_kwargs):
        assert "东海岸" not in revision.chapters[0].content_text
        return {"events": [], "memories": []}

    monkeypatch.setattr(
        "app.services.story.story_novel_chapter_service."
        "NarrativeExtractionService.extract",
        extract_rewritten,
    )
    resumed = anyio.run(
        generate_or_resume_chapter, service, revision, task, row, regenerate
    )

    updated = revision.continuity_ledger["chapters"]["1"]
    assert calls == ["body", "audit"]
    assert "东海岸" not in resumed.content_text
    assert resumed.content_hash != invalid_body_hash
    assert updated["body_hash"] == resumed.content_hash
    assert updated["source_hash"] == novel_chapter_source_hash(resumed)
    assert (updated["status"], updated["extraction_status"]) == ("ready", "ready")


@pytest.mark.parametrize(
    ("status", "validation_status", "body_hash"),
    [
        ("gate_failed", "failed", "current"),
        ("stale", "passed", "current"),
        ("ready", "passed", "mismatch"),
    ],
)
def test_generic_extraction_rejects_untrusted_v2_chapter(
    db_session,
    status,
    validation_status,
    body_hash,
):
    _user, story, service, revision, _task, *_ = _setup(db_session)
    row = _plan_row()
    _v2_revision(revision, row)
    chapter = service.checkpoint_chapter(
        revision,
        position=1,
        title="第一章",
        content_text="正文" * 1500,
        summary="摘要",
        cliffhanger=None,
    )
    source_hash = novel_chapter_source_hash(chapter)
    revision.continuity_ledger = {
        "chapters": {
            "1": {
                "status": status,
                "state_validation": {"status": validation_status},
                "body_hash": (
                    chapter.content_hash if body_hash == "current" else "stale-body"
                ),
                "source_hash": source_hash,
            }
        }
    }
    db_session.commit()

    with pytest.raises(ConflictError, match="未通过当前 Canon/状态门禁"):
        NarrativeExtractionService(NarrativeMemoryRepository(db_session))._source(
            story, "novel_chapter", chapter.business_id
        )
