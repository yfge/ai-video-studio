from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.services.narrative_memory.extraction_candidates import (
    CLAIM_VERIFICATION_VERSION,
)
from app.services.narrative_memory.source_hash import novel_chapter_source_hash
from app.services.story.story_novel_canon_service import normalize_canon
from app.services.story.story_novel_chapter_service import source_candidates
from app.services.story.story_novel_generation_context import build_chapter_context
from app.services.story.story_novel_state_service import (
    apply_state_delta,
    initial_story_state,
    state_hash,
)
from tests.unit.test_story_novel_longform import _canon, _plan_row, _setup


def test_context_contains_only_prior_valid_revision_candidates(db_session):
    _user, story, service, revision, _task, virtual_ip, character = _setup(
        db_session, with_character=True
    )
    event_quote = "主角发现裂缝"
    memory_quote = event_quote
    first = service.checkpoint_chapter(
        revision,
        position=1,
        title="第一章",
        content_text=f"{event_quote}。{memory_quote}。" + "前" * 3000,
        summary="发现裂缝",
        cliffhanger="门后有声音",
    )
    future = service.checkpoint_chapter(
        revision,
        position=3,
        title="第三章",
        content_text="后" * 3000,
        summary="未来",
        cliffhanger=None,
    )
    repo = NarrativeMemoryRepository(db_session)
    source_hash = novel_chapter_source_hash(first)
    canon = normalize_canon(_canon())
    state_before = initial_story_state(canon)
    state_delta = {
        "occurred_event_ids": ["event-1"],
        "state_transitions": [],
        "knowledge_grants": [
            {
                "character_id": character.business_id,
                "fact_id": "fact-crack",
                "source_event_id": "event-1",
            }
        ],
        "location_transitions": [],
        "milestones_consumed": [],
        "opened_thread_ids": [],
        "resolved_thread_ids": [],
        "evidence": {"event-1": event_quote},
        "knowledge_evidence": {
            f"{character.business_id}|fact-crack|event-1": memory_quote
        },
    }
    state_after = apply_state_delta(state_before, state_delta)
    revision.generation_plan = {
        "schema": "story_novel_generation_plan.v2",
        "version": 2,
        "status": "ready",
        "phase": "ready",
        "canon": canon,
        "canon_hash": canon["canon_hash"],
        "chapters": [_plan_row(1), _plan_row(2)],
    }
    revision.continuity_ledger = {
        "schema": "story_novel_continuity.v3",
        "current_state": state_after,
        "chapters": {
            "1": {
                "status": "ready",
                "body_hash": first.content_hash,
                "source_hash": source_hash,
                "canon_hash": canon["canon_hash"],
                "state_before_hash": state_hash(state_before),
                "state_after_hash": state_hash(state_after),
                "state_delta": state_delta,
                "state_validation": {"status": "passed", "violations": []},
            }
        },
    }
    anchor = repo.create_anchor(
        story_id=story.id,
        story_business_id=story.business_id,
        canon_branch_id="main",
        anchor_type="chapter",
        chapter_business_id=first.business_id,
        narrative_sequence=1000,
        source_artifact_type="novel_chapter",
        source_artifact_business_id=first.business_id,
        source_version=1,
        source_hash=source_hash,
    )
    repo.flush()
    event = repo.create_event(
        story_id=story.id,
        story_business_id=story.business_id,
        canon_branch_id="main",
        event_type="reveal",
        summary=event_quote,
        occurred_at_anchor_business_id=anchor.business_id,
        status="candidate",
        source_artifact_type="novel_chapter",
        source_artifact_business_id=first.business_id,
        source_version=1,
        source_hash=source_hash,
        candidate_evidence={
            "source_quote": event_quote,
            "source_quote_verified": True,
            "claim_verified": True,
            "claim_mode": "extractive",
            "verification_version": CLAIM_VERIFICATION_VERSION,
            "participant_binding_verified": True,
            "typed_event_ids": ["event-1"],
        },
    )
    unverified = repo.create_event(
        story_id=story.id,
        story_business_id=story.business_id,
        canon_branch_id="main",
        event_type="reveal",
        summary="旧链路未验证事实",
        occurred_at_anchor_business_id=anchor.business_id,
        status="candidate",
        source_artifact_type="novel_chapter",
        source_artifact_business_id=first.business_id,
        source_version=1,
        source_hash=source_hash,
    )
    unlisted = repo.create_event(
        story_id=story.id,
        story_business_id=story.business_id,
        canon_branch_id="main",
        event_type="reveal",
        summary=event_quote,
        occurred_at_anchor_business_id=anchor.business_id,
        status="candidate",
        source_artifact_type="novel_chapter",
        source_artifact_business_id=first.business_id,
        source_version=1,
        source_hash=source_hash,
        candidate_evidence={
            "source_quote": event_quote,
            "source_quote_verified": True,
            "claim_verified": True,
            "claim_mode": "extractive",
            "verification_version": CLAIM_VERIFICATION_VERSION,
            "participant_binding_verified": True,
            "typed_event_ids": ["event-1"],
        },
    )
    memory = repo.create_memory(
        story_id=story.id,
        story_business_id=story.business_id,
        canon_branch_id="main",
        character_business_id=character.business_id,
        virtual_ip_id=virtual_ip.id,
        virtual_ip_business_id=virtual_ip.business_id,
        scope="story_private",
        memory_type="witnessed",
        content=memory_quote,
        learned_at_anchor_business_id=anchor.business_id,
        effective_from_anchor_business_id=anchor.business_id,
        status="candidate",
        source_artifact_type="novel_chapter",
        source_artifact_business_id=first.business_id,
        source_version=1,
        source_hash=source_hash,
        candidate_evidence={
            "source_quote": memory_quote,
            "source_quote_verified": True,
            "claim_verified": True,
            "claim_mode": "typed_state_bound",
            "verification_version": CLAIM_VERIFICATION_VERSION,
            "typed_state_binding_verified": True,
            "typed_character_id": character.business_id,
            "typed_fact_id": "fact-crack",
            "typed_source_event_id": "event-1",
        },
    )
    future_event = repo.create_event(
        story_id=story.id,
        story_business_id=story.business_id,
        canon_branch_id="main",
        event_type="reveal",
        summary="未来真相",
        occurred_at_anchor_business_id=anchor.business_id,
        status="candidate",
        source_artifact_type="novel_chapter",
        source_artifact_business_id=future.business_id,
        source_version=1,
        source_hash=novel_chapter_source_hash(future),
    )
    repo.flush()
    ledger = dict(revision.continuity_ledger or {})
    rows = dict(ledger.get("chapters") or {})
    first_entry = dict(rows["1"])
    first_entry["event_ids"] = [event.business_id]
    first_entry["memory_ids"] = [memory.business_id]
    rows["1"] = first_entry
    ledger["chapters"] = rows
    revision.continuity_ledger = ledger
    repo.commit()
    source_events, source_memories = source_candidates(db_session, revision, first)
    assert [item.business_id for item in source_events] == [
        event.business_id,
        unlisted.business_id,
    ]
    assert [item.business_id for item in source_memories] == [memory.business_id]
    context = build_chapter_context(service, revision, 2, _plan_row(2))
    evidence = context["evidence"]
    assert evidence["event_ids"] == [event.business_id]
    assert unverified.business_id not in evidence["event_ids"]
    assert unlisted.business_id not in evidence["event_ids"]
    assert evidence["memory_ids"] == [memory.business_id]
    assert future_event.business_id not in evidence["event_ids"]
    assert evidence["event_hashes"] == [source_hash]
    assert evidence["context_chars"] <= 32000
