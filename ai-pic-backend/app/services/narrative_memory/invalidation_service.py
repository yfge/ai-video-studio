"""Propagate source-hash changes without replacing production artifacts."""

from datetime import datetime

from app.models.script import Story
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository


class NarrativeMemoryInvalidationService:
    def __init__(self, repo: NarrativeMemoryRepository):
        self.repo = repo

    def mark_source_changed(
        self,
        story: Story,
        *,
        artifact_business_id: str,
        source_before_hash: str | None,
        source_after_hash: str,
        commit: bool = True,
    ) -> dict:
        affected = []
        reason = {
            "reason_code": "source_hash_changed",
            "source_before_hash": source_before_hash,
            "source_after_hash": source_after_hash,
            "detected_at": datetime.utcnow().isoformat(),
        }
        candidates = [
            *self.repo.list_events(story.id),
            *self.repo.list_private_memories(story.id),
        ]
        for item in candidates:
            if (
                item.source_artifact_business_id == artifact_business_id
                and item.source_hash != source_after_hash
                and item.status not in {"rejected", "superseded"}
            ):
                item.status = "stale"
                item.invalidation = reason
                affected.append(item.business_id)

        stale_snapshots = []
        for snapshot in self.repo.list_snapshots(story.id):
            if set(snapshot.included_memory_ids or []) & set(affected):
                snapshot.is_stale = True
                snapshot.stale_reason = reason
                stale_snapshots.append(snapshot.business_id)
        if affected:
            story.memory_review_status = "review_required"
            for episode in self.repo.list_story_episodes(story.id):
                if episode.memory_snapshot_evidence:
                    episode.memory_snapshot_stale = True
                    episode.memory_snapshot_stale_reason = reason
            for script in self.repo.list_story_scripts(story.id):
                metadata = dict(script.extra_metadata or {})
                metadata["narrative_memory_stale"] = reason
                script.extra_metadata = metadata
        if commit:
            self.repo.commit()
        return {
            "affected_candidate_ids": affected,
            "stale_snapshot_ids": stale_snapshots,
        }

    def mark_baseline_changed(
        self,
        story: Story,
        *,
        baseline_before_hash: str | None,
        baseline_after_hash: str | None,
        commit: bool = True,
    ) -> dict:
        reason = {
            "reason_code": "shared_baseline_changed",
            "source_before_hash": baseline_before_hash,
            "source_after_hash": baseline_after_hash,
            "detected_at": datetime.utcnow().isoformat(),
        }
        snapshots = self.repo.list_snapshots(story.id)
        for snapshot in snapshots:
            snapshot.is_stale = True
            snapshot.stale_reason = reason
        for episode in self.repo.list_story_episodes(story.id):
            if episode.memory_snapshot_evidence:
                episode.memory_snapshot_stale = True
                episode.memory_snapshot_stale_reason = reason
        for script in self.repo.list_story_scripts(story.id):
            metadata = dict(script.extra_metadata or {})
            metadata["narrative_memory_stale"] = reason
            script.extra_metadata = metadata
        story.memory_review_status = "review_required"
        if commit:
            self.repo.commit()
        return {"stale_snapshot_ids": [item.business_id for item in snapshots]}
