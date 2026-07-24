from functools import partial

import anyio
import pytest
from app.core.exceptions import ConflictError
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.services.narrative_memory.extraction_service import NarrativeExtractionService
from app.services.narrative_memory.source_hash import novel_chapter_source_hash
from app.services.story.story_novel_chapter_service import generate_or_resume_chapter
from fastapi import HTTPException
from tests.unit.test_story_novel_canon_state import _body, _delta, _v2_revision
from tests.unit.test_story_novel_longform import _plan_row, _setup
from tests.unit.test_story_novel_resume_extraction_boundaries import (
    _allow_empty_candidate_set,
    _empty_extraction,
)


def test_generic_extraction_rejects_placeholder_v2_and_accepts_legacy(db_session):
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
    canon_hash = revision.generation_plan["canon_hash"]
    revision.continuity_ledger = {
        "chapters": {
            "1": {
                "status": "body_ready",
                "state_validation": {"status": "passed"},
                "body_hash": chapter.content_hash,
                "source_hash": source_hash,
                "canon_hash": canon_hash,
                "context_hash": "context-hash",
                "state_before_hash": "before-hash",
                "state_after_hash": "after-hash",
            }
        }
    }
    db_session.commit()
    extractor = NarrativeExtractionService(NarrativeMemoryRepository(db_session))

    with pytest.raises(ConflictError, match="未通过当前 Canon/状态门禁"):
        extractor._source(story, "novel_chapter", chapter.business_id)

    revision.generation_plan = {"schema": "story_novel_generation_plan.v1"}
    revision.continuity_ledger = {}
    db_session.commit()
    anchors, _source = extractor._source(story, "novel_chapter", chapter.business_id)
    assert anchors[0].source_hash == source_hash


def test_gate_failure_force_stales_same_source_candidates(db_session, monkeypatch):
    _allow_empty_candidate_set(monkeypatch)
    user, story, service, revision, task, *_ = _setup(db_session)
    row = _plan_row()
    _v2_revision(revision, row)
    db_session.commit()
    monkeypatch.setattr(
        "app.services.story.story_novel_chapter_service."
        "NarrativeExtractionService.extract",
        _empty_extraction,
    )

    async def valid(_revision, prompt, **_kwargs):
        return _delta() if "从实际小说正文提取" in prompt else _body()

    chapter = anyio.run(
        generate_or_resume_chapter,
        service,
        revision,
        task,
        row,
        valid,
    )
    source_hash = novel_chapter_source_hash(chapter)
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
        source_hash=source_hash,
    )
    repo.flush()
    event = repo.create_event(
        story_id=story.id,
        story_business_id=story.business_id,
        canon_branch_id="main",
        event_type="reveal",
        summary="同源旧候选",
        occurred_at_anchor_business_id=anchor.business_id,
        status="candidate",
        source_artifact_type="novel_chapter",
        source_artifact_business_id=chapter.business_id,
        source_version=1,
        source_hash=source_hash,
        candidate_evidence={"source_quote": "正文", "source_quote_verified": True},
        created_by=user.id,
    )
    repo.commit()

    async def fail_gate(_revision, prompt, **_kwargs):
        return (
            _delta(world_rule_violations=["rule-violation"])
            if "从实际小说正文提取" in prompt
            else _body()
        )

    with pytest.raises(HTTPException, match="Canon/状态门禁失败"):
        anyio.run(
            partial(
                generate_or_resume_chapter,
                service,
                revision,
                task,
                row,
                fail_gate,
                force=True,
            )
        )

    assert event.status == "stale"
    assert event.invalidation["reason_code"] == "chapter_gate_failed"
