"""Project approved-ready generic v5 events/perspectives into legacy candidates."""

from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.schemas.narrative_memory import (
    CandidateDeltaCreate,
    CharacterMemoryCandidateCreate,
    NarrativeEventCandidateCreate,
)
from app.services.narrative_memory.candidate_service import CandidateService
from app.services.narrative_memory.source_hash import novel_chapter_source_hash


def project_v5_candidates(service, revision, chapters, ledger_rows) -> set[str]:
    repo = NarrativeMemoryRepository(service.db)
    entity_characters = _entity_character_map(repo, revision)
    perspectives = {
        item["id"]: item
        for item in (revision.generation_plan or {})["consistency_schema"].get(
            "perspectives"
        )
        or []
    }
    projected = set()
    for chapter in chapters:
        entry = ledger_rows[str(chapter.position)]
        existing = _existing_projection(repo, revision, chapter)
        expected = _expected_projection_ids(entry, perspectives, entity_characters)
        if expected.issubset(existing):
            projected.update(existing.values())
            continue
        anchor = _chapter_anchor(repo, revision, chapter)
        service.db.flush()
        payload = _payload(
            chapter,
            entry,
            anchor.business_id,
            perspectives,
            entity_characters,
            existing,
        )
        created = CandidateService(repo).ingest(
            revision.story, payload, service.user, commit=False
        )
        projected.update(item.business_id for item in created["events"])
        projected.update(item.business_id for item in created["memories"])
        projected.update(existing.values())
    return projected


def project_v5_revision(service, revision, chapters, ledger_rows):
    return project_v5_candidates(service, revision, chapters, ledger_rows)


def _payload(chapter, entry, anchor_id, perspectives, characters, existing):
    evidence = {item["id"]: item for item in entry.get("evidence") or []}
    source_hash = novel_chapter_source_hash(chapter)
    events = []
    for event in entry.get("events") or []:
        projection_id = f"event:{event['id']}"
        if projection_id in existing:
            continue
        quote = _quote(event, evidence)
        participants = sorted(
            {
                characters[entity_id]["character_business_id"]
                for ids in (event.get("role_bindings") or {}).values()
                for entity_id in ids
                if entity_id in characters
            }
        )
        events.append(
            NarrativeEventCandidateCreate(
                event_type="action",
                summary=quote,
                participant_character_ids=participants,
                occurred_at_anchor_business_id=anchor_id,
                source_artifact_type="novel_chapter",
                source_artifact_business_id=chapter.business_id,
                source_version=1,
                source_hash=source_hash,
                candidate_evidence=_candidate_evidence(
                    projection_id, event, evidence, quote
                ),
            )
        )
    memories = []
    for claim in entry.get("perspective_changes") or []:
        perspective = perspectives.get(claim.get("perspective_id")) or {}
        character = characters.get(perspective.get("holder_entity_id"))
        projection_id = f"perspective:{claim['id']}"
        if not character or projection_id in existing:
            continue
        quote = _quote(claim, evidence)
        memories.append(
            CharacterMemoryCandidateCreate(
                character_business_id=character["character_business_id"],
                virtual_ip_business_id=character["virtual_ip_business_id"],
                memory_type="inferred",
                content=quote,
                belief=str(claim.get("value")),
                belief_confidence=0.7,
                occurred_at_anchor_business_id=anchor_id,
                learned_at_anchor_business_id=anchor_id,
                effective_from_anchor_business_id=anchor_id,
                source_artifact_type="novel_chapter",
                source_artifact_business_id=chapter.business_id,
                source_version=1,
                source_hash=source_hash,
                candidate_evidence=_candidate_evidence(
                    projection_id, claim, evidence, quote
                ),
            )
        )
    return CandidateDeltaCreate(events=events, memories=memories)


def _candidate_evidence(projection_id, row, evidence, quote):
    rows = [evidence[item] for item in row.get("evidence_ids") or []]
    return {
        "schema": "story_novel_v5_projection.v1",
        "projection_id": projection_id,
        "source_quote": quote,
        "source_quote_verified": True,
        "claim_verified": True,
        "verification_version": 1,
        "generic_evidence_ids": [item["id"] for item in rows],
        "sentence_ids": rows[0]["sentence_ids"],
    }


def _quote(row, evidence):
    quotes = [
        evidence[item]["quote"]
        for item in row.get("evidence_ids") or []
        if item in evidence
    ]
    if not quotes:
        raise ValueError(f"v5 projection {row.get('id')} lacks source evidence")
    return quotes[0]


def _entity_character_map(repo, revision):
    entities = {
        item["id"]: item
        for item in (revision.generation_plan or {})["initial_fact_graph"].get(
            "entities"
        )
        or []
    }
    rows = [
        item
        for item in repo.list_story_characters(revision.story_id)
        if item.virtual_ip
    ]
    by_key = {
        str(key): item
        for item in rows
        for key in (
            item.business_id,
            item.virtual_ip.business_id,
            item.display_name,
        )
        if key
    }
    result = {}
    for entity_id, entity in entities.items():
        match = by_key.get(entity_id) or by_key.get(entity.get("name"))
        if match:
            result[entity_id] = {
                "character_business_id": match.business_id,
                "virtual_ip_business_id": match.virtual_ip.business_id,
            }
    return result


def _expected_projection_ids(entry, perspectives, characters):
    result = {f"event:{item['id']}" for item in entry.get("events") or []}
    result.update(
        f"perspective:{item['id']}"
        for item in entry.get("perspective_changes") or []
        if characters.get(
            (perspectives.get(item.get("perspective_id")) or {}).get("holder_entity_id")
        )
    )
    return result


def _existing_projection(repo, revision, chapter):
    result = {}
    for item in [
        *repo.list_events(revision.story_id),
        *repo.list_private_memories(revision.story_id),
    ]:
        evidence = item.candidate_evidence or {}
        if (
            item.status in {"candidate", "approved"}
            and item.source_artifact_business_id == chapter.business_id
            and item.source_hash == novel_chapter_source_hash(chapter)
            and evidence.get("schema") == "story_novel_v5_projection.v1"
            and evidence.get("projection_id")
        ):
            result[evidence["projection_id"]] = item.business_id
    return result


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
