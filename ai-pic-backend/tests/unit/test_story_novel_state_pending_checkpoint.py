import anyio
from app.services.story.story_novel_chapter_service import generate_or_resume_chapter
from tests.unit.test_story_novel_state_pending_resume import (
    EVENT_QUOTE,
    _audit,
    _empty_extraction,
    _enter_pending,
    _fixture,
)


def test_evidence_only_failure_checkpoints_body_then_resumes_state_only(
    db_session, monkeypatch
):
    service, revision, task, row = _fixture(db_session)
    narrative_calls = 0

    async def extracted(*_args, **_kwargs):
        nonlocal narrative_calls
        narrative_calls += 1
        return await _empty_extraction()

    monkeypatch.setattr(
        "app.services.story.story_novel_chapter_service."
        "NarrativeExtractionService.extract",
        extracted,
    )
    monkeypatch.setattr(
        "app.services.story.story_novel_candidate_checkpoint."
        "complete_novel_candidate_set",
        lambda *_args: True,
    )
    saved_body, saved_hash = _enter_pending(service, revision, task, row)
    pending = revision.continuity_ledger["chapters"]["1"]
    assert pending["status"] == "state_pending"
    assert pending["state_pending_reason"] == "source_evidence"
    assert pending["extraction_status"] == "blocked"
    assert all(
        pending[key] is None
        for key in (
            "state_delta",
            "state_after",
            "state_after_hash",
            "plot_delta",
            "plot_delta_source",
            "plot_delta_version",
        )
    )
    assert revision.continuity_ledger["recovery_from_position"] == 1
    assert "current_state" not in revision.continuity_ledger
    audit_calls = 0

    async def state_only(_revision, prompt, **_kwargs):
        nonlocal audit_calls
        assert "从实际小说正文提取" in prompt
        audit_calls += 1
        return _audit(EVENT_QUOTE)

    chapter = anyio.run(
        generate_or_resume_chapter, service, revision, task, row, state_only
    )
    entry = revision.continuity_ledger["chapters"]["1"]
    assert (audit_calls, narrative_calls) == (1, 1)
    assert (chapter.content_text, chapter.content_hash) == (saved_body, saved_hash)
    assert entry["status"] == "ready"
    assert entry["state_validation"] == {"status": "passed", "violations": []}
    assert entry["state_after"]["subjects"]["zero-wind-key"] == {
        "location": "sand-port",
        "owner_id": "li-yan",
        "status": "已移交",
    }
    assert {
        key: value["knowledge"]
        for key, value in entry["state_after"]["subjects"].items()
        if key in {"chu-lan", "li-yan", "pei-heng"}
    } == {
        "chu-lan": ["fact-transfer-recorded"],
        "li-yan": ["fact-custody-received"],
        "pei-heng": ["fact-transfer-witnessed"],
    }
    assert entry["plot_delta"]["character_states"]["zero-wind-key"] == {
        "status": "已移交",
        "owner_id": "li-yan",
    }
    assert "recovery_from_position" not in revision.continuity_ledger
