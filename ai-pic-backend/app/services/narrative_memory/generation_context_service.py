"""Freeze deterministic narrative-memory evidence for downstream generation."""

import hashlib
import json
from typing import Any

from app.models.script import Episode, Story
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.services.narrative_memory.snapshot_service import SnapshotService


class NarrativeGenerationContextService:
    def __init__(self, repo: NarrativeMemoryRepository):
        self.repo = repo

    def latest_context(self, story: Story) -> dict[str, Any] | None:
        if story.memory_mode != "story_scoped_memory_v1":
            return None
        anchors = self.repo.list_anchors(story.id)
        anchor = anchors[-1] if anchors else self._seed_anchor(story)
        return self._build_context(story, anchor)

    def chapter_context(
        self,
        story: Story,
        *,
        revision_business_id: str,
        position: int,
        persist_snapshots: bool = True,
    ) -> dict[str, Any] | None:
        if story.memory_mode != "story_scoped_memory_v1":
            return None
        source = {"revision_business_id": revision_business_id, "position": position}
        anchor = self._artifact_anchor(
            story,
            anchor_type="chapter",
            narrative_sequence=max(0, position * 1000 - 1),
            source_artifact_type="novel_chapter_start",
            source_artifact_business_id=f"{revision_business_id}:{position}",
            source_version=1,
            source_hash=self._hash(source),
        )
        return self._build_context(story, anchor, persist_snapshots=persist_snapshots)

    def freeze_episode(
        self,
        story: Story,
        episode: Episode,
        *,
        adaptation_plan_version: int | None = None,
        commit: bool = True,
    ) -> dict[str, Any] | None:
        if story.memory_mode != "story_scoped_memory_v1":
            return None
        source = {
            "episode_business_id": episode.business_id,
            "episode_number": episode.episode_number,
            "source_chapter_refs": episode.source_chapter_refs or [],
            "adaptation_plan_version": adaptation_plan_version,
            "ledger_hash": story.memory_ledger_hash,
        }
        anchor = self._artifact_anchor(
            story,
            anchor_type="episode",
            narrative_sequence=1_000_000 + int(episode.episode_number or 0) * 10_000,
            source_artifact_type="episode",
            source_artifact_business_id=episode.business_id,
            source_version=int(adaptation_plan_version or 1),
            source_hash=self._hash(source),
            episode_business_id=episode.business_id,
        )
        context = self._build_context(story, anchor)
        episode.memory_snapshot_evidence = context
        episode.memory_ledger_version = int(story.memory_ledger_version or 0)
        episode.memory_ledger_hash = story.memory_ledger_hash
        episode.disclosure_policy = context["audience_disclosure"]
        episode.memory_snapshot_stale = False
        episode.memory_snapshot_stale_reason = None
        if commit:
            self.repo.commit()
        return context

    def _build_context(
        self, story: Story, anchor, *, persist_snapshots: bool = True
    ) -> dict[str, Any]:
        snapshots = []
        for character in self.repo.list_story_characters(story.id):
            if not character.virtual_ip:
                continue
            snapshot_service = SnapshotService(self.repo)
            method = (
                snapshot_service.rebuild
                if persist_snapshots
                else snapshot_service.preview
            )
            snapshot = method(
                story,
                character_business_id=character.business_id,
                as_of_anchor_business_id=anchor.business_id,
                **({"commit": False} if persist_snapshots else {}),
            )
            snapshots.append(self._snapshot_payload(story, snapshot))
        events = self._events_before(story, anchor.narrative_sequence)
        disclosure = {
            "allowed_reveal": [
                item["business_id"]
                for item in events
                if item["audience_disclosure"] == "revealed"
            ],
            "must_hide": [
                item["business_id"]
                for item in events
                if item["audience_disclosure"] == "hidden"
            ],
            "must_advance": [
                item["business_id"]
                for item in events
                if item["audience_disclosure"] in {"hinted", "partial"}
            ],
        }
        self.repo.flush()
        return {
            "schema": "narrative_generation_context.v1",
            "story_business_id": story.business_id,
            "as_of_anchor_business_id": anchor.business_id,
            "memory_ledger_version": int(story.memory_ledger_version or 0),
            "memory_ledger_hash": story.memory_ledger_hash,
            "character_snapshots": snapshots,
            "approved_events": events,
            "audience_disclosure": disclosure,
        }

    def _snapshot_payload(self, story: Story, snapshot) -> dict[str, Any]:
        included = set(snapshot.included_memory_ids or [])
        private = [
            {
                "business_id": item.business_id,
                "content": item.content,
                "belief": item.belief,
                "memory_type": item.memory_type,
                "effective_from_anchor_business_id": item.effective_from_anchor_business_id,
            }
            for item in self.repo.list_character_memories(
                story.id, snapshot.character_business_id, status="approved"
            )
            if item.business_id in included
        ]
        shared = []
        for character in (story.shared_memory_baseline or {}).get("characters") or []:
            if (
                character.get("virtual_ip_business_id")
                != snapshot.virtual_ip_business_id
            ):
                continue
            shared.extend(
                item
                for item in character.get("memories") or []
                if item.get("business_id") in included
            )
        return {
            "snapshot_business_id": snapshot.business_id,
            "snapshot_hash": snapshot.snapshot_hash,
            "character_business_id": snapshot.character_business_id,
            "virtual_ip_business_id": snapshot.virtual_ip_business_id,
            "included_memory_ids": snapshot.included_memory_ids,
            "memories": [*shared, *private],
            "growth_state": snapshot.growth_state,
        }

    def _events_before(self, story: Story, sequence: int) -> list[dict[str, Any]]:
        anchors = {item.business_id: item for item in self.repo.list_anchors(story.id)}
        events = []
        for item in self.repo.list_events(story.id, status="approved"):
            anchor = anchors.get(item.occurred_at_anchor_business_id)
            if not anchor or anchor.narrative_sequence > sequence:
                continue
            events.append(
                {
                    "business_id": item.business_id,
                    "summary": item.summary,
                    "event_type": item.event_type,
                    "presentation": item.presentation,
                    "audience_disclosure": item.audience_disclosure,
                    "occurred_at_anchor_business_id": item.occurred_at_anchor_business_id,
                }
            )
        return events

    def _seed_anchor(self, story: Story):
        seed = story.story_seed or {"title": story.title, "synopsis": story.synopsis}
        return self._artifact_anchor(
            story,
            anchor_type="chapter",
            narrative_sequence=0,
            source_artifact_type="story_seed",
            source_artifact_business_id=story.business_id,
            source_version=int(story.story_seed_version or 1),
            source_hash=self._hash(seed),
        )

    def _artifact_anchor(self, story: Story, **data):
        existing = next(
            (
                item
                for item in self.repo.list_anchors(story.id)
                if item.source_artifact_type == data["source_artifact_type"]
                and item.source_artifact_business_id
                == data["source_artifact_business_id"]
                and item.source_hash == data["source_hash"]
            ),
            None,
        )
        if existing:
            return existing
        anchor = self.repo.create_anchor(
            story_id=story.id,
            story_business_id=story.business_id,
            canon_branch_id=story.canon_branch_id or "main",
            **data,
        )
        self.repo.flush()
        return anchor

    @staticmethod
    def _hash(value: Any) -> str:
        raw = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()
