"""Atomic candidate replacement and canonical-revision isolation helpers."""

from datetime import datetime

from app.core.exceptions import ConflictError
from app.models.task import TaskStatus
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.services.narrative_memory.source_hash import novel_chapter_source_hash

from .story_novel_task_guard import NovelTaskCancelled


def extraction_checkpoint_fingerprint(revision, chapter) -> tuple:
    plan = revision.generation_plan or {}
    entry = ((revision.continuity_ledger or {}).get("chapters") or {}).get(
        str(chapter.position)
    ) or {}
    return (
        revision.id,
        revision.lifecycle_status,
        revision.task_id,
        plan.get("schema"),
        plan.get("version"),
        plan.get("plan_hash"),
        plan.get("outline_hash"),
        plan.get("canon_hash"),
        chapter.id,
        chapter.business_id,
        chapter.position,
        chapter.content_hash,
        chapter.review_status,
        novel_chapter_source_hash(chapter),
        entry.get("status"),
        entry.get("body_hash"),
        entry.get("source_hash"),
        entry.get("context_hash"),
        entry.get("canon_hash"),
        entry.get("state_before_hash"),
        entry.get("extraction_status"),
        tuple(entry.get("event_ids") or []),
        tuple(entry.get("memory_ids") or []),
    )


def lock_extraction_checkpoint(
    service,
    revision,
    chapter,
    task,
    expected_fingerprint: tuple,
) -> None:
    if task is not None:
        locked_task = service.repo.task(task.id, for_update=True)
        if not locked_task or locked_task.status == TaskStatus.CANCELLED:
            raise NovelTaskCancelled()
    locked_revision = service.repo.accessible_revision(
        revision.business_id,
        service.user,
        with_chapters=False,
        for_update=True,
    )
    locked_chapter = service.repo.chapter(
        revision.id,
        chapter.business_id,
        for_update=True,
    )
    if (
        not locked_revision
        or not locked_chapter
        or extraction_checkpoint_fingerprint(locked_revision, locked_chapter)
        != expected_fingerprint
    ):
        raise ConflictError("章节提取期间正文、计划或 checkpoint 已变化，请重试")


def active_source_candidate_ids(
    db,
    story_id: int,
    chapter_business_id: str,
    source_hash: str,
) -> set[str]:
    repo = NarrativeMemoryRepository(db)
    return {
        item.business_id
        for item in [
            *repo.list_events(story_id),
            *repo.list_private_memories(story_id),
        ]
        if item.status in {"candidate", "approved"}
        and item.source_artifact_business_id == chapter_business_id
        and item.source_hash == source_hash
    }


def candidate_batch_matches_source(
    chapter,
    events: list,
    memories: list,
) -> bool:
    source_hash = novel_chapter_source_hash(chapter)
    entities = [*events, *memories]
    ids = [item.business_id for item in entities]
    return len(ids) == len(set(ids)) and all(
        item.status in {"candidate", "approved"}
        and item.source_artifact_business_id == chapter.business_id
        and item.source_hash == source_hash
        for item in entities
    )


def stale_replaced_candidates(
    db,
    story_id: int,
    previous_ids: set[str],
    replacement_ids: set[str],
) -> None:
    repo = NarrativeMemoryRepository(db)
    reason = {
        "reason_code": "candidate_claim_contract_upgraded",
        "detected_at": datetime.utcnow().isoformat(),
    }
    for business_id in previous_ids - replacement_ids:
        entity = repo.get_event(story_id, business_id) or repo.get_memory(
            story_id, business_id
        )
        if entity and entity.status in {"candidate", "approved"}:
            entity.status = "stale"
            entity.invalidation = reason


def retire_revision_candidates(db, story, chapter_business_ids: set[str]) -> bool:
    """Remove a replaced canonical revision from the global approved ledger."""
    if not chapter_business_ids:
        return False
    repo = NarrativeMemoryRepository(db)
    reason = {
        "reason_code": "canonical_novel_revision_replaced",
        "detected_at": datetime.utcnow().isoformat(),
    }
    affected = []
    affected_memories = []
    for entity in [
        *repo.list_events(story.id),
        *repo.list_private_memories(story.id),
    ]:
        if (
            entity.source_artifact_business_id in chapter_business_ids
            and entity.status in {"candidate", "approved"}
        ):
            entity.status = "superseded"
            entity.invalidation = reason
            affected.append(entity.business_id)
            if not hasattr(entity, "summary"):
                affected_memories.append(entity.business_id)
    for snapshot in repo.list_snapshots(story.id):
        if set(snapshot.included_memory_ids or []) & set(affected_memories):
            snapshot.is_stale = True
            snapshot.stale_reason = reason
    if affected:
        story.memory_review_status = "review_required"
        for episode in repo.list_story_episodes(story.id):
            if episode.memory_snapshot_evidence:
                episode.memory_snapshot_stale = True
                episode.memory_snapshot_stale_reason = reason
        for script in repo.list_story_scripts(story.id):
            metadata = dict(script.extra_metadata or {})
            metadata["narrative_memory_stale"] = reason
            script.extra_metadata = metadata
    return bool(affected)
