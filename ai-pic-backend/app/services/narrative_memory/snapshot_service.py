"""Deterministic, story-isolated memory snapshot builder."""

import hashlib
import json
from typing import Any

from app.core.exceptions import NotFoundError
from app.models.script import Story
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository


class SnapshotService:
    def __init__(self, repo: NarrativeMemoryRepository):
        self.repo = repo

    def rebuild(
        self,
        story: Story,
        *,
        character_business_id: str,
        as_of_anchor_business_id: str,
        commit: bool = True,
    ):
        character = self.repo.get_story_character(story.id, character_business_id)
        if not character or not character.virtual_ip:
            raise NotFoundError("故事角色", character_business_id)
        target = self.repo.get_anchor(story.id, as_of_anchor_business_id)
        if not target:
            raise NotFoundError("叙事锚点", as_of_anchor_business_id)
        anchors = {item.business_id: item for item in self.repo.list_anchors(story.id)}
        private = self.repo.list_character_memories(
            story.id, character_business_id, status="approved"
        )
        applicable = [
            item
            for item in private
            if self._is_effective(item, target.narrative_sequence, anchors)
        ]
        shared = self._frozen_shared(story, character.virtual_ip.business_id)
        included = self._included_items(applicable, shared, anchors)
        growth = self._growth_state(applicable)
        payload = {
            "story_business_id": story.business_id,
            "canon_branch_id": story.canon_branch_id or "main",
            "character_business_id": character_business_id,
            "virtual_ip_business_id": character.virtual_ip.business_id,
            "as_of_anchor_business_id": as_of_anchor_business_id,
            "shared_baseline_version": int(story.shared_memory_baseline_version or 0),
            "approved_memory_watermark": int(story.memory_ledger_version or 0),
            "included_memory_ids": [item["business_id"] for item in included],
            "growth_state": growth,
        }
        snapshot_hash = self.stable_hash(payload)
        snapshot = self.repo.create_snapshot(
            story_id=story.id,
            snapshot_hash=snapshot_hash,
            **payload,
        )
        if commit:
            self.repo.commit()
            self.repo.refresh(snapshot)
        return snapshot

    @staticmethod
    def stable_hash(payload: dict[str, Any]) -> str:
        raw = json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @staticmethod
    def _is_effective(memory, target_sequence: int, anchors: dict) -> bool:
        effective = anchors.get(memory.effective_from_anchor_business_id)
        if not effective or effective.narrative_sequence > target_sequence:
            return False
        if memory.invalidated_at_anchor_business_id:
            invalidated = anchors.get(memory.invalidated_at_anchor_business_id)
            if invalidated and invalidated.narrative_sequence <= target_sequence:
                return False
        return True

    @staticmethod
    def _frozen_shared(story: Story, virtual_ip_business_id: str) -> list[dict]:
        baseline = story.shared_memory_baseline or {}
        characters = baseline.get("characters") if isinstance(baseline, dict) else []
        for item in characters or []:
            if item.get("virtual_ip_business_id") == virtual_ip_business_id:
                return list(item.get("memories") or [])
        return []

    @staticmethod
    def _included_items(private: list, shared: list[dict], anchors: dict) -> list[dict]:
        private_items = [
            {
                "business_id": item.business_id,
                "sequence": getattr(
                    anchors.get(item.effective_from_anchor_business_id),
                    "narrative_sequence",
                    0,
                ),
            }
            for item in private
        ]
        shared_items = [
            {"business_id": item["business_id"], "sequence": -1}
            for item in shared
            if item.get("business_id")
        ]
        return sorted(
            private_items + shared_items,
            key=lambda item: (item["sequence"], item["business_id"]),
        )

    @staticmethod
    def _growth_state(memories: list) -> dict[str, Any]:
        state: dict[str, Any] = {
            "current_goals": [],
            "values": [],
            "wounds": [],
            "abilities": [],
            "relationships": {},
            "growth_stage": None,
            "source_memory_ids": [],
        }
        for memory in memories:
            delta = (memory.candidate_evidence or {}).get("growth_delta") or {}
            for key in ("current_goals", "values", "wounds", "abilities"):
                for value in delta.get(key) or []:
                    if value not in state[key]:
                        state[key].append(value)
            state["relationships"].update(delta.get("relationships") or {})
            if delta.get("growth_stage"):
                state["growth_stage"] = delta["growth_stage"]
            state["source_memory_ids"].append(memory.business_id)
        return state
