"""Revision-local Narrative Event and Character Memory context."""

from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.services.narrative_memory.candidate_verification import (
    verified_novel_candidate,
)
from app.services.narrative_memory.source_hash import novel_chapter_source_hash

from .story_novel_domain import active_chapters


def _source_hashes(prior_rows: list) -> dict:
    return {item.business_id: novel_chapter_source_hash(item) for item in prior_rows}


def revision_local_candidates(
    db, revision, position: int, *, prior_chapters=None
) -> tuple[list[dict], list[dict]]:
    prior_rows = (
        prior_chapters
        if prior_chapters is not None
        else ready_prior_chapters(revision, position)
    )
    source_hashes = _source_hashes(prior_rows)
    chapters_by_id = {item.business_id: item for item in prior_rows}
    ledger_rows = (revision.continuity_ledger or {}).get("chapters") or {}
    strict = (revision.generation_plan or {}).get(
        "schema"
    ) == "story_novel_generation_plan.v2"

    def verified(item) -> bool:
        if not strict:
            return (item.candidate_evidence or {}).get("source_quote_verified") is True
        chapter = chapters_by_id.get(item.source_artifact_business_id)
        return bool(
            chapter
            and verified_novel_candidate(
                item,
                chapter,
                ledger_rows.get(str(chapter.position)) or {},
                require_ledger_membership=True,
            )
        )

    repo = NarrativeMemoryRepository(db)
    events = [
        {
            "business_id": item.business_id,
            "source_chapter_business_id": item.source_artifact_business_id,
            "source_hash": item.source_hash,
            "event_type": item.event_type,
            "summary": item.summary,
            "participant_character_ids": item.participant_character_ids or [],
            "presentation": item.presentation,
            "audience_disclosure": item.audience_disclosure,
            "source_quote": (item.candidate_evidence or {}).get("source_quote"),
        }
        for item in repo.list_events(revision.story_id)
        if item.status in {"candidate", "approved"}
        and source_hashes.get(item.source_artifact_business_id) == item.source_hash
        and verified(item)
    ]
    memories = [
        {
            "business_id": item.business_id,
            "source_chapter_business_id": item.source_artifact_business_id,
            "source_hash": item.source_hash,
            "character_business_id": item.character_business_id,
            "memory_type": item.memory_type,
            "content": item.content,
            "belief": item.belief,
            "effective_from_anchor_business_id": (
                item.effective_from_anchor_business_id
            ),
            "growth_delta": (item.candidate_evidence or {}).get("growth_delta"),
            "source_quote": (item.candidate_evidence or {}).get("source_quote"),
        }
        for item in repo.list_private_memories(revision.story_id)
        if item.status in {"candidate", "approved"}
        and source_hashes.get(item.source_artifact_business_id) == item.source_hash
        and verified(item)
    ]
    return events, memories


def ready_prior_chapters(revision, position: int, *, strict=False) -> list:
    chapters = {
        item.position: item
        for item in active_chapters(revision)
        if item.position < position
    }
    if (revision.generation_plan or {}).get(
        "schema"
    ) != "story_novel_generation_plan.v2":
        return [chapters[key] for key in sorted(chapters)]
    ledger_rows = (revision.continuity_ledger or {}).get("chapters") or {}
    result = []
    for prior_position in range(1, position):
        chapter = chapters.get(prior_position)
        entry = ledger_rows.get(str(prior_position)) or {}
        valid = (
            chapter is not None
            and entry.get("status") == "ready"
            and entry.get("body_hash") == chapter.content_hash
            and entry.get("source_hash") == novel_chapter_source_hash(chapter)
        )
        if not valid:
            if strict:
                raise ValueError(f"第 {prior_position} 章正文或来源 hash 前缀不完整")
            break
        result.append(chapter)
    return result
