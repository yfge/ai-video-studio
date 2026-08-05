import copy
from types import SimpleNamespace

import pytest
from app.services.narrative_consistency import validate_chapter_transition
from app.services.narrative_memory.source_hash import novel_chapter_source_hash
from app.services.story.story_novel_domain import sha256_text
from app.services.story.story_novel_sentence_spans import (
    sentence_index_hash,
    sentence_spans,
)
from app.services.story.story_novel_v5_plan import freeze_v5_plan
from app.services.story.story_novel_v5_resume import validate_v5_chain
from fastapi import HTTPException
from tests.unit.test_story_novel_v5_plan import (
    _base_plan,
    _compile_payload,
    _snapshot,
)


def test_resume_replays_ready_claims_and_rejects_evidence_or_snapshot_tampering():
    plan, revision = _ready_revision()

    final = validate_v5_chain(revision, plan["chapters"])

    assert (
        final["snapshot_hash"]
        == revision.continuity_ledger["chapters"]["1"]["snapshot_after_hash"]
    )

    entry = revision.continuity_ledger["chapters"]["1"]
    entry["evidence"][0]["source_artifact_id"] = "another-chapter"
    with pytest.raises(HTTPException, match="evidence 来源版本/hash 不匹配"):
        validate_v5_chain(revision, plan["chapters"])

    entry["evidence"][0]["source_artifact_id"] = revision.chapters[0].business_id
    entry["snapshot_after_hash"] = "tampered"
    with pytest.raises(HTTPException, match="状态 hash 不匹配"):
        validate_v5_chain(revision, plan["chapters"])


def _ready_revision():
    base = copy.deepcopy(_base_plan())
    base["chapters"][0].update(min_chars=1, target_chars=8, max_chars=30)
    plan = freeze_v5_plan(base, _compile_payload(), _snapshot(), [])
    content = "A选择了新方向。"
    chapter = SimpleNamespace(
        position=1,
        title=plan["chapters"][0]["title"],
        content_text=content,
        content_hash=sha256_text(content),
        business_id="chapter-1",
        review_status="ready",
        is_deleted=False,
    )
    source_hash = novel_chapter_source_hash(chapter)
    evidence = {
        "id": "evidence-1",
        "source_artifact_type": "novel_chapter",
        "source_artifact_id": chapter.business_id,
        "source_version": 1,
        "source_hash": source_hash,
        "sentence_ids": ["S0001"],
        "quote": content,
    }
    claim = {
        "id": "claim-1",
        "operation": "replace",
        "subject_id": "a",
        "predicate_id": "selects",
        "value": "new",
        "source_event_id": "event-1",
        "evidence_ids": ["evidence-1"],
    }
    event = {
        "id": "event-1",
        "event_type_id": "changes",
        "role_bindings": {"actor": ["a"], "target": ["new"]},
        "evidence_ids": ["evidence-1"],
    }
    delta = {
        "schema": "story_novel_claim_delta.v1",
        "claims": [claim],
        "perspective_changes": [],
        "occurred_events": [event],
        "evidence": [evidence],
    }
    sentences = sentence_spans(content)
    transition = validate_chapter_transition(
        plan["consistency_schema"],
        plan["initial_fact_graph"],
        delta,
        sentences,
        allowed_event_ids={"event-1"},
        event_catalog={"event-1": plan["causal_event_graph"]["events"][0]},
    )
    entry = {
        "status": "ready",
        "extraction_status": "ready",
        "body_hash": chapter.content_hash,
        "source_hash": source_hash,
        "plan_hash": plan["plan_hash"],
        "schema_hash": plan["consistency_schema_hash"],
        "snapshot_before_hash": plan["initial_snapshot_hash"],
        "snapshot_after_hash": transition["graph_after"]["snapshot_hash"],
        "sentence_index_hash": sentence_index_hash(sentences),
        "readability_report": {"status": "passed"},
        "consistency_report": {"status": "passed"},
        "length_report": {"status": "passed"},
        "claims": [claim],
        "events": [event],
        "perspective_changes": [],
        "evidence": [evidence],
    }
    revision = SimpleNamespace(
        generation_plan=plan,
        story_snapshot=_snapshot(),
        chapters=[chapter],
        continuity_ledger={"chapters": {"1": entry}},
    )
    return plan, revision
