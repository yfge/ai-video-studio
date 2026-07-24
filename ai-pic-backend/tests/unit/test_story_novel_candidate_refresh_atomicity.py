import anyio
import pytest
from app.core.exceptions import ConflictError, ServiceError
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.services.narrative_memory.extraction_service import NarrativeExtractionService
from app.services.narrative_memory.source_hash import novel_chapter_source_hash
from app.services.story import story_novel_candidate_checkpoint as checkpoint
from app.services.story.story_novel_chapter_service import ensure_chapter_extraction
from tests.unit.test_story_novel_longform import _plan_row, _setup


def _chapter_with_previous_candidate(db_session):
    user, story, service, revision, _task, *_ = _setup(db_session)
    row = _plan_row()
    revision.generation_plan = {
        "status": "ready",
        "chapter_count": 1,
        "target_chars": 3000,
        "chapters": [row],
    }
    revision.chapter_count = 1
    chapter = service.checkpoint_chapter(
        revision,
        position=1,
        title="第一章",
        content_text="正文" * 1500,
        summary="发现线索",
        cliffhanger=None,
    )
    repo = NarrativeMemoryRepository(db_session)
    source_hash = novel_chapter_source_hash(chapter)
    anchor = repo.create_anchor(
        story_id=story.id,
        story_business_id=story.business_id,
        canon_branch_id="main",
        anchor_type="chapter",
        narrative_sequence=1000,
        source_artifact_type="novel_chapter",
        source_artifact_business_id=chapter.business_id,
        source_version=1,
        source_hash=source_hash,
    )
    repo.flush()
    previous = repo.create_event(
        story_id=story.id,
        story_business_id=story.business_id,
        canon_branch_id="main",
        event_type="reveal",
        summary="旧链路候选",
        occurred_at_anchor_business_id=anchor.business_id,
        status="candidate",
        source_artifact_type="novel_chapter",
        source_artifact_business_id=chapter.business_id,
        source_version=1,
        source_hash=source_hash,
        candidate_evidence={"source_quote_verified": True},
        created_by=user.id,
    )
    repo.flush()
    entry = {
        "status": "body_ready",
        "body_hash": chapter.content_hash,
        "source_hash": source_hash,
        "extraction_status": "pending",
        "event_ids": [previous.business_id],
        "memory_ids": [],
    }
    ledger = dict(revision.continuity_ledger)
    ledger["chapters"] = {"1": entry}
    revision.continuity_ledger = ledger
    repo.commit()
    return user, story, service, revision, chapter, repo, anchor, previous


def test_failed_claim_upgrade_keeps_previous_candidates_until_replacement(
    db_session, monkeypatch
):
    (
        user,
        story,
        service,
        revision,
        chapter,
        repo,
        anchor,
        previous,
    ) = _chapter_with_previous_candidate(db_session)
    source_hash = novel_chapter_source_hash(chapter)

    async def fail(*_args, **_kwargs):
        raise ServiceError("replacement failed")

    monkeypatch.setattr(NarrativeExtractionService, "extract", fail)
    with pytest.raises(ServiceError, match="replacement failed"):
        anyio.run(ensure_chapter_extraction, service, revision, chapter)

    db_session.refresh(previous)
    assert previous.status == "candidate"
    assert revision.continuity_ledger["chapters"]["1"]["event_ids"] == [
        previous.business_id
    ]

    replacement_id = None

    async def replace(*_args, **_kwargs):
        nonlocal replacement_id
        replacement = repo.create_event(
            story_id=story.id,
            story_business_id=story.business_id,
            canon_branch_id="main",
            event_type="reveal",
            summary="正文正文",
            occurred_at_anchor_business_id=anchor.business_id,
            status="candidate",
            source_artifact_type="novel_chapter",
            source_artifact_business_id=chapter.business_id,
            source_version=1,
            source_hash=source_hash,
            candidate_evidence={
                "source_quote": "正文正文",
                "source_quote_verified": True,
                "claim_verified": True,
                "claim_mode": "extractive",
                "verification_version": 2,
                "participant_binding_verified": True,
                "typed_event_ids": ["event-1"],
            },
            created_by=user.id,
        )
        repo.flush()
        replacement_id = replacement.business_id
        return {"events": [replacement], "memories": []}

    monkeypatch.setattr(NarrativeExtractionService, "extract", replace)
    anyio.run(ensure_chapter_extraction, service, revision, chapter)

    db_session.refresh(previous)
    assert previous.status == "stale"
    assert revision.continuity_ledger["chapters"]["1"]["event_ids"] == [replacement_id]


def test_final_checkpoint_commit_failure_rolls_back_replacement_and_ledger(
    db_session, monkeypatch
):
    (
        user,
        story,
        service,
        revision,
        chapter,
        repo,
        anchor,
        previous,
    ) = _chapter_with_previous_candidate(db_session)
    source_hash = novel_chapter_source_hash(chapter)
    replacement_id = None

    async def replace(*_args, **_kwargs):
        nonlocal replacement_id
        replacement = repo.create_event(
            story_id=story.id,
            story_business_id=story.business_id,
            canon_branch_id="main",
            event_type="reveal",
            summary="不会落库的新候选",
            occurred_at_anchor_business_id=anchor.business_id,
            status="candidate",
            source_artifact_type="novel_chapter",
            source_artifact_business_id=chapter.business_id,
            source_version=1,
            source_hash=source_hash,
            created_by=user.id,
        )
        repo.flush()
        replacement_id = replacement.business_id
        return {"events": [replacement], "memories": []}

    original_commit = service.db.commit

    def fail_commit():
        raise RuntimeError("final checkpoint commit failed")

    monkeypatch.setattr(NarrativeExtractionService, "extract", replace)
    monkeypatch.setattr(service.db, "commit", fail_commit)
    with pytest.raises(RuntimeError, match="final checkpoint commit failed"):
        anyio.run(ensure_chapter_extraction, service, revision, chapter)
    monkeypatch.setattr(service.db, "commit", original_commit)

    db_session.refresh(previous)
    db_session.refresh(revision)
    assert previous.status == "candidate"
    assert revision.continuity_ledger["chapters"]["1"]["event_ids"] == [
        previous.business_id
    ]
    assert repo.get_event(story.id, replacement_id) is None


def test_v2_candidate_completeness_blocks_ready_checkpoint(db_session, monkeypatch):
    (
        _user,
        _story,
        service,
        revision,
        chapter,
        _repo,
        _anchor,
        previous,
    ) = _chapter_with_previous_candidate(db_session)
    plan = dict(revision.generation_plan)
    plan["schema"] = "story_novel_generation_plan.v2"
    revision.generation_plan = plan
    db_session.commit()
    checked = []

    async def empty_batch(*_args, **_kwargs):
        return {"events": [], "memories": []}

    def incomplete(entry, events, memories):
        checked.append((entry, events, memories))
        return False

    monkeypatch.setattr(NarrativeExtractionService, "extract", empty_batch)
    monkeypatch.setattr(checkpoint, "complete_novel_candidate_set", incomplete)
    with pytest.raises(ConflictError, match="候选集合未完整覆盖"):
        anyio.run(ensure_chapter_extraction, service, revision, chapter)

    db_session.refresh(previous)
    db_session.refresh(revision)
    assert len(checked) == 1
    assert previous.status == "candidate"
    assert revision.continuity_ledger["chapters"]["1"]["extraction_status"] == "pending"
