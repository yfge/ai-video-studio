import anyio
import pytest
from app.services.narrative_memory.source_hash import novel_chapter_source_hash
from app.services.story.story_novel_chapter_service import generate_or_resume_chapter
from app.services.story.story_novel_generation_context import build_chapter_context
from app.services.story.story_novel_state_pending_preflight import (
    pending_checkpoint_reusable,
)
from fastapi import HTTPException
from tests.unit.test_story_novel_state_pending_resume import (
    INVALID_QUOTE,
    _audit,
    _empty_extraction,
    _enter_pending,
    _fixture,
)


def _persist_pending_checkpoint(service, revision):
    chapter = service.checkpoint_chapter(
        revision,
        position=1,
        title="第一章",
        content_text="待恢复正文" * 800,
        summary="待恢复",
        cliffhanger=None,
    )
    revision.continuity_ledger = {
        "chapters": {
            "1": {
                "status": "state_pending",
                "chapter_business_id": chapter.business_id,
                "body_hash": chapter.content_hash,
                "source_hash": novel_chapter_source_hash(chapter),
                "context_hash": "drifted",
                "extraction_status": "blocked",
            }
        },
        "state_status": "failed",
        "recovery_from_position": 1,
    }
    service.db.commit()
    return chapter


def test_repeated_evidence_only_resume_keeps_pending_without_prose(
    db_session, monkeypatch
):
    service, revision, task, row = _fixture(db_session)
    monkeypatch.setattr(
        "app.services.story.story_novel_chapter_service."
        "NarrativeExtractionService.extract",
        _empty_extraction,
    )
    saved_body, saved_hash = _enter_pending(service, revision, task, row)
    audit_calls = 0

    async def invalid_state_only(_revision, prompt, **_kwargs):
        nonlocal audit_calls
        assert "从实际小说正文提取" in prompt
        audit_calls += 1
        return _audit(INVALID_QUOTE)

    with pytest.raises(HTTPException, match="状态提取待恢复"):
        anyio.run(
            generate_or_resume_chapter,
            service,
            revision,
            task,
            row,
            invalid_state_only,
        )
    entry = revision.continuity_ledger["chapters"]["1"]
    chapter = revision.chapters[0]
    assert audit_calls == 2
    assert (chapter.content_text, chapter.content_hash) == (saved_body, saved_hash)
    assert entry["status"] == "state_pending"
    assert entry["state_extraction_repair_count"] == 2
    assert "current_state" not in revision.continuity_ledger


def test_pending_hash_drift_fails_closed_without_regenerating_prose(
    db_session, monkeypatch
):
    service, revision, task, row = _fixture(db_session)
    monkeypatch.setattr(
        "app.services.story.story_novel_chapter_service."
        "NarrativeExtractionService.extract",
        _empty_extraction,
    )
    chapter = _persist_pending_checkpoint(service, revision)
    saved_hash = chapter.content_hash
    calls = []

    async def must_not_generate(*_args, **_kwargs):
        calls.append("provider")
        raise AssertionError("普通 Resume 不得改写 state_pending 正文")

    with pytest.raises(HTTPException) as exc_info:
        anyio.run(
            generate_or_resume_chapter,
            service,
            revision,
            task,
            row,
            must_not_generate,
        )
    assert "正文未改写" in exc_info.value.detail
    chapter = revision.chapters[0]
    assert calls == []
    assert chapter.content_hash == saved_hash
    assert revision.continuity_ledger["chapters"]["1"]["status"] == "state_pending"


def test_pending_preflight_fails_closed_for_malformed_persisted_plan(
    db_session, monkeypatch
):
    service, revision, task, row = _fixture(db_session)
    monkeypatch.setattr(
        "app.services.story.story_novel_chapter_service."
        "NarrativeExtractionService.extract",
        _empty_extraction,
    )
    _persist_pending_checkpoint(service, revision)
    context_pack = build_chapter_context(service, revision, 1, row)
    entry = revision.continuity_ledger["chapters"]["1"]
    chapter = revision.chapters[0]
    revision.generation_plan = {
        **revision.generation_plan,
        "chapters": [None],
    }

    assert not pending_checkpoint_reusable(
        revision,
        chapter,
        entry,
        context_pack,
        row,
    )
