"""Freeze, diff, and manually synchronize shared-memory baselines."""

import hashlib
import json

from app.core.exceptions import ConflictError, ValidationError
from app.models.script import Story
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.repositories.narrative_promotion_repository import NarrativePromotionRepository
from app.services.narrative_memory.invalidation_service import (
    NarrativeMemoryInvalidationService,
)


class BaselineService:
    def __init__(
        self,
        memory_repo: NarrativeMemoryRepository,
        promotion_repo: NarrativePromotionRepository,
    ):
        self.memory_repo = memory_repo
        self.promotion_repo = promotion_repo

    def freeze(self, story: Story, *, commit: bool = True) -> dict:
        baseline = self._current_baseline(story)
        story.shared_memory_baseline = baseline
        story.shared_memory_baseline_version = baseline["version"]
        story.shared_memory_baseline_hash = baseline["hash"]
        if commit:
            self.memory_repo.commit()
            self.memory_repo.refresh(story)
        return baseline

    def diff(self, story: Story) -> dict:
        current = self._current_baseline(story)
        frozen = story.shared_memory_baseline or {"characters": []}
        old = self._memory_map(frozen)
        new = self._memory_map(current)
        return {
            "frozen_version": int(story.shared_memory_baseline_version or 0),
            "available_version": current["version"],
            "frozen_hash": story.shared_memory_baseline_hash,
            "available_hash": current["hash"],
            "added": [new[key] for key in sorted(new.keys() - old.keys())],
            "removed": [old[key] for key in sorted(old.keys() - new.keys())],
            "modified": [
                {"before": old[key], "after": new[key]}
                for key in sorted(old.keys() & new.keys())
                if old[key] != new[key]
            ],
            "has_updates": current["hash"] != story.shared_memory_baseline_hash,
        }

    def sync(self, story: Story, *, expected_version: int, confirm: bool) -> dict:
        if not confirm:
            raise ValidationError("同步公共记忆基线需要明确确认")
        actual = int(story.shared_memory_baseline_version or 0)
        if actual != expected_version:
            raise ConflictError(
                "Story 公共记忆基线已变化",
                context={
                    "expected_version": expected_version,
                    "actual_version": actual,
                },
            )
        before_hash = story.shared_memory_baseline_hash
        baseline = self.freeze(story, commit=False)
        NarrativeMemoryInvalidationService(self.memory_repo).mark_baseline_changed(
            story,
            baseline_before_hash=before_hash,
            baseline_after_hash=story.shared_memory_baseline_hash,
            commit=False,
        )
        self.memory_repo.commit()
        self.memory_repo.refresh(story)
        return baseline

    def _current_baseline(self, story: Story) -> dict:
        characters = []
        max_version = 0
        for character in self.memory_repo.list_story_characters(story.id):
            if not character.virtual_ip:
                continue
            memories = self.promotion_repo.list_shared_memories(
                character.virtual_ip_id,
                canon_branch_id=story.canon_branch_id or "main",
            )
            memory_data = [
                {
                    "business_id": item.business_id,
                    "version": item.version,
                    "content": item.content,
                    "belief": item.belief,
                    "memory_type": item.memory_type,
                    "source_hash": item.source_hash,
                }
                for item in memories
            ]
            max_version = max(max_version, *(item.version for item in memories), 0)
            characters.append(
                {
                    "character_business_id": character.business_id,
                    "virtual_ip_business_id": character.virtual_ip.business_id,
                    "memories": memory_data,
                }
            )
        body = {"version": max_version, "characters": characters}
        raw = json.dumps(
            body, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        return {**body, "hash": hashlib.sha256(raw.encode()).hexdigest()}

    @staticmethod
    def _memory_map(baseline: dict) -> dict[str, dict]:
        return {
            memory["business_id"]: memory
            for character in baseline.get("characters") or []
            for memory in character.get("memories") or []
            if memory.get("business_id")
        }
