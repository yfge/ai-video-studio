import json

import anyio
import pytest
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.services.narrative_memory.source_hash import novel_chapter_source_hash
from app.services.story.story_novel_chapter_service import generate_or_resume_chapter
from app.services.story.story_novel_domain import sha256_text
from app.services.story.story_novel_prose_canon_gate import (
    revision_prose_canon_violations,
)
from fastapi import HTTPException
from tests.unit.test_story_novel_canon_state import _body, _delta, _v2_revision
from tests.unit.test_story_novel_chapter_state_gate import (
    _coastal_body,
    _install_dryland_canon,
)
from tests.unit.test_story_novel_longform import _plan_row, _setup


async def _empty_extraction(*_args, **_kwargs):
    return {"events": [], "memories": []}


def test_invalid_ready_resume_checkpoint_is_preserved_before_provider(
    db_session, monkeypatch
):
    user, story, service, revision, task, *_ = _setup(db_session)
    first_plan = _plan_row(1)
    second_plan = _plan_row(2)
    _v2_revision(revision, first_plan)
    revision.generation_plan = {
        **dict(revision.generation_plan),
        "version": 4,
        "chapter_count": 2,
        "target_chars": 6000,
        "chapters": [first_plan, second_plan],
    }
    revision.chapter_count = 2
    _install_dryland_canon(revision)
    db_session.commit()
    monkeypatch.setattr(
        "app.services.story.story_novel_chapter_service."
        "NarrativeExtractionService.extract",
        _empty_extraction,
    )
    monkeypatch.setattr(
        "app.services.story.story_novel_candidate_checkpoint."
        "complete_novel_candidate_set",
        lambda *_args: True,
    )

    async def initial(_revision, prompt, **_kwargs):
        if "从实际小说正文提取" not in prompt:
            return _body()
        delta = json.loads(_delta())
        delta["future_event_audit"] = {"event-2": "not_present"}
        return json.dumps(delta, ensure_ascii=False)

    chapter = anyio.run(
        generate_or_resume_chapter,
        service,
        revision,
        task,
        first_plan,
        initial,
    )
    future = service.checkpoint_chapter(
        revision,
        position=2,
        title="第二章",
        content_text="后续正文" * 1000,
        summary="后续摘要",
        cliffhanger=None,
    )
    invalid = json.loads(_coastal_body())
    invalid["content_text"] = "东海岸。" + invalid["content_text"]
    chapter.content_text = invalid["content_text"]
    chapter.content_hash = sha256_text(chapter.content_text)
    invalid_source_hash = novel_chapter_source_hash(chapter)

    ledger = dict(revision.continuity_ledger)
    entries = dict(ledger["chapters"])
    current = dict(entries["1"])
    current.update(
        status="ready",
        extraction_status="ready",
        body_hash=chapter.content_hash,
        source_hash=invalid_source_hash,
        event_ids=[],
        memory_ids=[],
    )
    future_entry = dict(current)
    future_entry.update(
        chapter_business_id=future.business_id,
        body_hash=future.content_hash,
        source_hash=novel_chapter_source_hash(future),
    )
    entries.update({"1": current, "2": future_entry})
    ledger["chapters"] = entries
    revision.continuity_ledger = ledger
    plan_rows = [dict(item) for item in revision.generation_plan["chapters"]]
    for row in plan_rows:
        row.update(generation_status="ready", extraction_status="ready")
    revision.generation_plan = {
        **dict(revision.generation_plan),
        "chapters": plan_rows,
    }

    repo = NarrativeMemoryRepository(db_session)
    anchor = repo.create_anchor(
        story_id=story.id,
        story_business_id=story.business_id,
        canon_branch_id="main",
        anchor_type="chapter",
        narrative_sequence=1000,
        source_artifact_type="novel_chapter",
        source_artifact_business_id=chapter.business_id,
        source_version=1,
        source_hash=invalid_source_hash,
    )
    repo.flush()
    event = repo.create_event(
        story_id=story.id,
        story_business_id=story.business_id,
        canon_branch_id="main",
        event_type="reveal",
        summary="旧正文候选",
        occurred_at_anchor_business_id=anchor.business_id,
        status="candidate",
        source_artifact_type="novel_chapter",
        source_artifact_business_id=chapter.business_id,
        source_version=1,
        source_hash=invalid_source_hash,
        candidate_evidence={"source_quote": "东海岸", "source_quote_verified": True},
        created_by=user.id,
    )
    repo.commit()

    violations = revision_prose_canon_violations(
        revision, first_plan, chapter.content_text
    )
    assert any("海岸" in item["message"] for item in violations)
    provider_calls = 0

    async def provider_failure(*_args, **_kwargs):
        nonlocal provider_calls
        provider_calls += 1
        raise AssertionError("普通 Resume 不得重写 ready 正文")

    with pytest.raises(HTTPException, match="ready checkpoint"):
        anyio.run(
            generate_or_resume_chapter,
            service,
            revision,
            task,
            first_plan,
            provider_failure,
        )

    db_session.rollback()
    db_session.refresh(revision)
    db_session.refresh(chapter)
    db_session.refresh(future)
    db_session.refresh(event)
    rows = revision.continuity_ledger["chapters"]
    assert provider_calls == 0
    assert rows["1"]["status"] == rows["2"]["status"] == "ready"
    assert rows["1"]["extraction_status"] == "ready"
    assert event.status == "candidate"
    assert [
        (row["generation_status"], row["extraction_status"])
        for row in revision.generation_plan["chapters"]
    ] == [("ready", "ready"), ("ready", "ready")]
