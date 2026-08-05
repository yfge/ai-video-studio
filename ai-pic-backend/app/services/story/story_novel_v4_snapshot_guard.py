"""Post-provider CAS for immutable v4 planner snapshots."""

from __future__ import annotations

from fastapi import HTTPException

from .story_novel_candidate_context import (
    ready_prior_chapters,
    revision_local_candidates,
)
from .story_novel_v4_plan_reset import mark_snapshot_stale


def lock_current_snapshot_source(service, revision, snapshot: dict):
    """Lock and compare fingerprints only; never rebuild model context."""
    locked = service.repo.revision_by_id(revision.id, for_update=True)
    position = int(snapshot.get("position") or 0)
    plan = dict((locked or revision).generation_plan or {})
    reason = None
    if locked is None:
        reason = "revision disappeared"
    elif snapshot.get("generation_plan_hash") != plan.get("plan_hash"):
        reason = "generation plan hash changed during model call"
    elif snapshot.get("canon_hash") != plan.get("canon_hash"):
        reason = "canon hash changed during model call"
    elif not source_manifest_current(
        service, locked, position, snapshot.get("source_manifest") or {}
    ):
        reason = "planner source manifest changed during model call"
    if reason:
        if locked is not None and position > 0:
            mark_snapshot_stale(service, locked, position, reason)
        raise HTTPException(status_code=409, detail=f"第 {position} 章 {reason}")
    return locked


def lock_chapter_execution_source(service, revision, entry: dict):
    snapshot = {
        **entry["planner_snapshot"],
        "generation_plan_hash": entry["execution_generation_plan_hash"],
    }
    return lock_current_snapshot_source(service, revision, snapshot)


def source_manifest_current(service, revision, position: int, manifest: dict) -> bool:
    try:
        previous = ready_prior_chapters(revision, position, strict=True)
        events, memories = revision_local_candidates(
            service.db, revision, position, prior_chapters=previous
        )
    except ValueError:
        return False
    if not _selected_sources_current(events, "event", manifest):
        return False
    if not _selected_sources_current(memories, "memory", manifest):
        return False
    current = {
        "chapter_ids": [item.business_id for item in previous],
        "chapter_hashes": [item.content_hash for item in previous],
        "candidate_universe": {
            "world_events": [
                {"id": item.get("business_id"), "source_hash": item.get("source_hash")}
                for item in events
            ],
            "character_memories": [
                {"id": item.get("business_id"), "source_hash": item.get("source_hash")}
                for item in memories
            ],
        },
    }
    return current == {
        "chapter_ids": manifest.get("chapter_ids") or [],
        "chapter_hashes": manifest.get("chapter_hashes") or [],
        "candidate_universe": manifest.get("candidate_universe")
        or {"world_events": [], "character_memories": []},
    }


def _selected_sources_current(rows, prefix: str, manifest: dict) -> bool:
    ids = list(manifest.get(f"{prefix}_ids") or [])
    hashes = list(manifest.get(f"{prefix}_hashes") or [])
    if len(ids) != len(hashes):
        return False
    available = {item.get("business_id"): item.get("source_hash") for item in rows}
    return all(
        available.get(business_id) == source_hash
        for business_id, source_hash in zip(ids, hashes, strict=True)
    )
