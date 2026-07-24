import json

import pytest
from app.core.exceptions import ConflictError
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.services.narrative_memory.extraction_service import NarrativeExtractionService
from app.services.narrative_memory.source_hash import novel_chapter_source_hash
from app.services.story.story_novel_canon_service import (
    CANON_GATE_VERSION,
    normalize_canon,
)
from app.services.story.story_novel_generation_context import build_chapter_context
from app.services.story.story_novel_length_service import generation_plan_hash
from app.services.story.story_novel_plot_contract import validated_plot_delta
from app.services.story.story_novel_state_service import apply_state_delta, state_hash
from tests.unit.test_story_novel_longform import _canon, _plan_row, _setup


def _checkpoint(db_session, *, body="正文" * 1500, world_rules=None):
    _user, story, service, revision, _task, *_ = _setup(db_session)
    raw_canon = _canon()
    raw_canon["world_rules"] = world_rules or []
    canon = normalize_canon(raw_canon, required_gate_version=CANON_GATE_VERSION)
    row = _plan_row()
    plan = {
        "schema": "story_novel_generation_plan.v2",
        "version": 4,
        "status": "ready",
        "phase": "ready",
        "canon": canon,
        "canon_hash": canon["canon_hash"],
        "canon_gate_version": CANON_GATE_VERSION,
        "chapter_count": 1,
        "chapters": [row],
    }
    plan["plan_hash"] = generation_plan_hash(plan)
    revision.generation_plan = plan
    chapter = service.checkpoint_chapter(
        revision,
        position=1,
        title="第一章",
        content_text=body,
        summary="摘要",
        cliffhanger=None,
    )
    context = build_chapter_context(service, revision, 1, row)
    delta = json.loads(
        json.dumps(
            {
                "occurred_event_ids": ["event-1"],
                "premature_future_event_ids": [],
                "state_transitions": [],
                "knowledge_grants": [],
                "location_transitions": [],
                "milestones_consumed": [],
                "opened_thread_ids": [],
                "resolved_thread_ids": [],
                "world_rule_violations": [],
                "evidence": {"event-1": "正文"},
            }
        )
    )
    state_after = apply_state_delta(context["state_before"], delta)
    evidence = context["evidence"]
    entry = {
        "status": "body_ready",
        "chapter_business_id": chapter.business_id,
        "body_hash": chapter.content_hash,
        "source_hash": novel_chapter_source_hash(chapter),
        "canon_hash": evidence["canon_hash"],
        "context_hash": evidence["context_hash"],
        "context_evidence": evidence,
        "state_before_hash": evidence["state_before_hash"],
        "state_after_hash": state_hash(state_after),
        "state_after": state_after,
        "state_delta": delta,
        "state_validation": {"status": "passed", "violations": []},
        "plot_delta": validated_plot_delta(row, delta),
        "plot_delta_source": "typed_state",
        "plot_delta_version": 1,
    }
    revision.continuity_ledger = {"chapters": {"1": entry}}
    db_session.commit()
    return story, chapter, entry


def _extractor(db_session):
    return NarrativeExtractionService(NarrativeMemoryRepository(db_session))


def test_public_extraction_accepts_replayable_v2_checkpoint(db_session):
    story, chapter, _entry = _checkpoint(db_session)

    anchors, source = _extractor(db_session)._source(
        story, "novel_chapter", chapter.business_id
    )

    assert anchors[0].source_hash == novel_chapter_source_hash(chapter)
    assert "正文" in source


def test_public_extraction_rejects_current_prose_canon_violation(db_session):
    story, chapter, _entry = _checkpoint(
        db_session,
        body="东海岸" * 1000,
        world_rules=[
            {
                "id": "rule-dryland",
                "statement": "旱海六城不存在海岸。",
                "exceptions": [],
            }
        ],
    )

    with pytest.raises(ConflictError, match="未通过当前 Canon/状态门禁"):
        _extractor(db_session)._source(story, "novel_chapter", chapter.business_id)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("context_hash", "placeholder-context"),
        ("state_before_hash", "placeholder-before"),
        ("state_after_hash", "placeholder-after"),
        ("state_delta", {}),
        ("plot_delta_source", None),
    ],
)
def test_public_extraction_rejects_non_replayable_checkpoint(db_session, field, value):
    story, chapter, entry = _checkpoint(db_session)
    entry[field] = value
    chapter.novel_export.continuity_ledger = {"chapters": {"1": entry}}
    db_session.commit()

    with pytest.raises(ConflictError, match="未通过当前 Canon/状态门禁"):
        _extractor(db_session)._source(story, "novel_chapter", chapter.business_id)
