"""Read models for the lightweight Story memory summary."""

from app.models.script import Story
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository


class NarrativeMemoryQueryService:
    def __init__(self, repo: NarrativeMemoryRepository):
        self.repo = repo

    def summary(self, story: Story) -> dict:
        memories = self.repo.list_private_memories(story.id)
        events = self.repo.list_events(story.id)
        pending = sum(item.status == "candidate" for item in [*memories, *events])
        stale = sum(item.status == "stale" for item in [*memories, *events])
        conflict = sum(
            bool((item.candidate_evidence or {}).get("conflicts"))
            for item in [*memories, *events]
        )
        latest = self.repo.latest_snapshot(story.id)
        return {
            "canon_branch_id": story.canon_branch_id or "main",
            "private_memory_count": len(memories),
            "shared_baseline_version": int(story.shared_memory_baseline_version or 0),
            "shared_baseline_hash": story.shared_memory_baseline_hash,
            "latest_snapshot_hash": latest.snapshot_hash if latest else None,
            "pending_count": pending,
            "conflict_count": conflict,
            "stale_count": stale,
            "memory_review_status": story.memory_review_status or "not_initialized",
        }
