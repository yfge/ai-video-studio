"""Deterministically materialize v3 events and memories from verified spans."""

from __future__ import annotations

from app.core.exceptions import ConflictError
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.schemas.narrative_memory import (
    CandidateDeltaCreate,
    CharacterMemoryCandidateCreate,
    NarrativeEventCandidateCreate,
)
from app.services.narrative_memory.candidate_service import CandidateService
from app.services.narrative_memory.candidate_verification import (
    complete_novel_candidate_set,
)
from app.services.narrative_memory.extraction_bindings import (
    knowledge_character_bindings,
)
from app.services.narrative_memory.knowledge_evidence import knowledge_evidence_key
from app.services.narrative_memory.source_hash import novel_chapter_source_hash

from .story_novel_candidate_refresh import (
    active_source_candidate_ids,
    candidate_batch_matches_source,
    extraction_checkpoint_fingerprint,
    lock_extraction_checkpoint,
    stale_replaced_candidates,
)
from .story_novel_revision_local_memory import local_memory_rows
from .story_novel_v3_candidate_evidence import (
    event_evidence,
    memory_evidence,
    participant_ids,
)


def materialize_v3_candidates(service, revision, chapter, task, entry: dict) -> dict:
    from .story_novel_chapter_service import (
        save_ledger_entry,
        sync_plan_chapter_runtime,
    )

    repo = NarrativeMemoryRepository(service.db)
    expected = extraction_checkpoint_fingerprint(revision, chapter)
    previous = active_source_candidate_ids(
        service.db,
        revision.story_id,
        chapter.business_id,
        novel_chapter_source_hash(chapter),
    )
    try:
        lock_extraction_checkpoint(service, revision, chapter, task, expected)
        anchor = _chapter_anchor(repo, revision, chapter)
        service.db.flush()
        characters = _characters(repo, revision)
        payload = _candidate_payload(
            revision, chapter, entry, anchor.business_id, characters
        )
        memory_grant_keys = _payload_memory_grant_keys(payload)
        created = CandidateService(repo).ingest(
            revision.story, payload, service.user, commit=False
        )
        events = list(created["events"])
        memories = list(created["memories"])
        if not candidate_batch_matches_source(chapter, events, memories):
            raise ConflictError("v3 候选不属于当前章节 checkpoint")
        candidate_entry = {
            **entry,
            "memory_grant_keys": [list(item) for item in sorted(memory_grant_keys)],
            "revision_local_memories": local_memory_rows(chapter, entry),
        }
        if not complete_novel_candidate_set(candidate_entry, events, memories):
            raise ConflictError("v3 候选未完整覆盖 expected delta")
        replacement = {item.business_id for item in [*events, *memories]}
        stale_replaced_candidates(service.db, revision.story_id, previous, replacement)
        entry.update(
            status="ready",
            stage="ready",
            extraction_status="ready",
            event_ids=[item.business_id for item in events],
            memory_ids=[item.business_id for item in memories],
            memory_grant_keys=candidate_entry["memory_grant_keys"],
            revision_local_memories=candidate_entry["revision_local_memories"],
        )
        save_ledger_entry(revision, chapter.position, entry)
        sync_plan_chapter_runtime(revision, chapter.position, entry)
        ledger = dict(revision.continuity_ledger or {})
        ledger.update(current_state=entry["state_after"], state_status="generating")
        revision.continuity_ledger = ledger
        chapter.review_status = "ready"
        service.db.commit()
        return entry
    except Exception:
        service.db.rollback()
        raise


def _candidate_payload(revision, chapter, entry, anchor_id, characters):
    delta = entry["state_delta"]
    source_hash = novel_chapter_source_hash(chapter)
    events = []
    for event_id in delta.get("occurred_event_ids") or []:
        quote = delta["evidence"][event_id]
        events.append(
            NarrativeEventCandidateCreate(
                event_type="action",
                summary=quote,
                participant_character_ids=participant_ids(
                    event_id, quote, entry, characters
                ),
                occurred_at_anchor_business_id=anchor_id,
                presentation="on_screen",
                audience_disclosure="revealed",
                source_artifact_type="novel_chapter",
                source_artifact_business_id=chapter.business_id,
                source_version=1,
                source_hash=source_hash,
                candidate_evidence=event_evidence(event_id, quote, entry),
            )
        )
    memories = _memory_candidates(
        revision, chapter, entry, anchor_id, source_hash, characters
    )
    return CandidateDeltaCreate(events=events, memories=memories)


def _memory_candidates(revision, chapter, entry, anchor_id, source_hash, characters):
    delta = entry["state_delta"]
    local_ids = set(
        ((entry.get("state_after") or {}).get("revision_local_entities") or {})
    )
    persisted_delta = {
        **delta,
        "knowledge_grants": [
            item
            for item in delta.get("knowledge_grants") or []
            if item.get("character_id") not in local_ids
        ],
    }
    bindings = knowledge_character_bindings(
        (revision.generation_plan or {}).get("canon") or {},
        persisted_delta,
        characters,
    )
    by_character = {item["character_business_id"]: item for item in characters}
    memories = []
    for character_id, binding in bindings.items():
        character = by_character[character_id]
        for grant in binding["grants"]:
            quote = delta["knowledge_evidence"][knowledge_evidence_key(grant)]
            memories.append(
                CharacterMemoryCandidateCreate(
                    character_business_id=character_id,
                    virtual_ip_business_id=character["virtual_ip_business_id"],
                    memory_type="witnessed",
                    content=quote,
                    salience=0.7,
                    occurred_at_anchor_business_id=anchor_id,
                    learned_at_anchor_business_id=anchor_id,
                    effective_from_anchor_business_id=anchor_id,
                    source_artifact_type="novel_chapter",
                    source_artifact_business_id=chapter.business_id,
                    source_version=1,
                    source_hash=source_hash,
                    candidate_evidence=memory_evidence(
                        revision, chapter, grant, quote, entry
                    ),
                )
            )
    return memories


def _characters(repo, revision):
    canon_characters = {
        str(name).strip(): item["id"]
        for item in ((revision.generation_plan or {}).get("canon") or {}).get(
            "entities"
        )
        or []
        if item.get("kind") == "character" and item.get("id")
        for name in [item.get("name"), *(item.get("aliases") or [])]
        if str(name or "").strip()
    }
    return [
        {
            "character_business_id": item.business_id,
            "virtual_ip_business_id": item.virtual_ip.business_id,
            "name": item.display_name,
            "canon_character_id": canon_characters.get(item.display_name),
        }
        for item in repo.list_story_characters(revision.story_id)
        if item.virtual_ip
    ]


def _payload_memory_grant_keys(payload) -> set[tuple[str, str, str]]:
    return {
        (
            evidence.get("typed_character_id"),
            evidence.get("typed_fact_id"),
            evidence.get("typed_source_event_id"),
        )
        for item in payload.memories
        for evidence in [item.candidate_evidence or {}]
    }


def _chapter_anchor(repo, revision, chapter):
    source_hash = novel_chapter_source_hash(chapter)
    existing = next(
        (
            item
            for item in repo.list_anchors(revision.story_id)
            if item.source_artifact_business_id == chapter.business_id
            and item.source_hash == source_hash
        ),
        None,
    )
    return existing or repo.create_anchor(
        story_id=revision.story_id,
        story_business_id=revision.story.business_id,
        canon_branch_id=revision.story.canon_branch_id or "main",
        anchor_type="chapter",
        chapter_business_id=chapter.business_id,
        narrative_sequence=chapter.position * 1000,
        source_artifact_type="novel_chapter",
        source_artifact_business_id=chapter.business_id,
        source_version=1,
        source_hash=source_hash,
    )
