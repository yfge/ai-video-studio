"""Candidate ingest, editing, review, and ledger versioning."""

import hashlib
import json
from datetime import datetime

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.script import Story
from app.models.user import User
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.schemas.narrative_memory import CandidateDeltaCreate, CandidateUpdate
from app.services.narrative_memory.access import require_version
from app.services.narrative_memory.anchor_service import AnchorService


class CandidateService:
    def __init__(self, repo: NarrativeMemoryRepository):
        self.repo = repo

    def ingest(
        self,
        story: Story,
        payload: CandidateDeltaCreate,
        user: User,
        *,
        commit: bool = True,
    ) -> dict:
        anchors = [
            AnchorService(self.repo).create(story, item, user.id, commit=False)
            for item in payload.anchors
        ]
        events = [
            self._create_event(story, item.model_dump(), user.id)
            for item in payload.events
        ]
        memories = [
            self._create_memory(story, item.model_dump(), user.id)
            for item in payload.memories
        ]
        if commit:
            self.repo.commit()
        else:
            self.repo.flush()
        return {"anchors": anchors, "events": events, "memories": memories}

    def _create_event(self, story: Story, data: dict, user_id: int):
        data.pop("candidate_kind", None)
        self._require_anchor(story, data["occurred_at_anchor_business_id"])
        return self.repo.create_event(
            story_id=story.id,
            story_business_id=story.business_id,
            canon_branch_id=story.canon_branch_id or "main",
            status="candidate",
            created_by=user_id,
            **data,
        )

    def _create_memory(self, story: Story, data: dict, user_id: int):
        data.pop("candidate_kind", None)
        character = self.repo.get_story_character(
            story.id, data["character_business_id"]
        )
        if not character or not character.virtual_ip:
            raise ValidationError("角色不属于当前 Story")
        if character.virtual_ip.business_id != data["virtual_ip_business_id"]:
            raise ValidationError("角色与 Virtual IP 不匹配")
        for field in (
            "occurred_at_anchor_business_id",
            "learned_at_anchor_business_id",
            "effective_from_anchor_business_id",
            "invalidated_at_anchor_business_id",
        ):
            if data.get(field):
                self._require_anchor(story, data[field])
        return self.repo.create_memory(
            story_id=story.id,
            story_business_id=story.business_id,
            canon_branch_id=story.canon_branch_id or "main",
            virtual_ip_id=character.virtual_ip_id,
            scope="story_private",
            status="candidate",
            created_by=user_id,
            **data,
        )

    def update(self, story: Story, business_id: str, payload: CandidateUpdate):
        kind, entity = self._candidate(story, business_id)
        require_version(entity, payload.expected_version)
        if entity.status not in {"candidate", "stale"}:
            raise ConflictError("只有候选或 stale 内容可以编辑")
        updates = payload.model_dump(exclude_unset=True, exclude={"expected_version"})
        if kind == "event":
            updates = {k: v for k, v in updates.items() if k in self._event_fields()}
        else:
            updates = {k: v for k, v in updates.items() if k in self._memory_fields()}
        required_anchor_fields = (
            ("occurred_at_anchor_business_id",)
            if kind == "event"
            else (
                "occurred_at_anchor_business_id",
                "learned_at_anchor_business_id",
                "effective_from_anchor_business_id",
            )
        )
        if any(
            updates.get(field, getattr(entity, field, None)) is None
            for field in required_anchor_fields
        ):
            raise ValidationError("候选内容的发生、获知和生效锚点不能为空")
        for field in (
            "occurred_at_anchor_business_id",
            "learned_at_anchor_business_id",
            "effective_from_anchor_business_id",
            "invalidated_at_anchor_business_id",
        ):
            if updates.get(field):
                self._require_anchor(story, updates[field])
        for field, value in updates.items():
            setattr(entity, field, value)
        entity.version = int(entity.version or 1) + 1
        self.repo.commit()
        self.repo.refresh(entity)
        return kind, entity

    def review(
        self,
        story: Story,
        business_id: str,
        *,
        expected_version: int,
        approved: bool,
        user_id: int,
        reason: str | None,
    ):
        kind, entity = self._candidate(story, business_id)
        require_version(entity, expected_version)
        if entity.status not in {"candidate", "stale"}:
            raise ConflictError("候选已被审核")
        entity.status = "approved" if approved else "rejected"
        entity.approved_by = user_id if approved else None
        entity.approved_at = datetime.utcnow() if approved else None
        if reason:
            evidence = dict(entity.candidate_evidence or {})
            evidence["review_reason"] = reason
            entity.candidate_evidence = evidence
        entity.version = int(entity.version or 1) + 1
        if approved:
            self._advance_ledger(story)
        self.repo.commit()
        self.repo.refresh(entity)
        return kind, entity

    def approve_source_candidates(
        self,
        story: Story,
        *,
        valid_sources: dict[str, str],
        user_id: int,
        require_verified_evidence: bool = False,
        eligible_candidate_ids: set[str] | None = None,
        commit: bool = True,
    ) -> list[str]:
        """Promote only candidates whose chapter ID and source hash are current."""
        promoted = []
        candidates = [
            *self.repo.list_events(story.id),
            *self.repo.list_private_memories(story.id),
        ]
        for entity in candidates:
            if (
                entity.status != "candidate"
                or (
                    eligible_candidate_ids is not None
                    and entity.business_id not in eligible_candidate_ids
                )
                or valid_sources.get(entity.source_artifact_business_id)
                != entity.source_hash
                or (
                    require_verified_evidence
                    and (entity.candidate_evidence or {}).get("source_quote_verified")
                    is not True
                )
            ):
                continue
            entity.status = "approved"
            entity.approved_by = user_id
            entity.approved_at = datetime.utcnow()
            entity.version = int(entity.version or 1) + 1
            promoted.append(entity.business_id)
        if promoted:
            self._advance_ledger(story)
        if commit:
            self.repo.commit()
        return promoted

    def _candidate(self, story: Story, business_id: str):
        event = self.repo.get_event(story.id, business_id)
        if event:
            return "event", event
        memory = self.repo.get_memory(story.id, business_id)
        if memory:
            return "memory", memory
        raise NotFoundError("叙事候选", business_id)

    def _require_anchor(self, story: Story, business_id: str) -> None:
        if not self.repo.get_anchor(story.id, business_id):
            raise ValidationError(f"锚点不属于当前 Story: {business_id}")

    def _advance_ledger(self, story: Story) -> None:
        story.memory_ledger_version = int(story.memory_ledger_version or 0) + 1
        approved = [
            ("event", item.business_id, item.source_hash, item.version)
            for item in self.repo.list_events(story.id, status="approved")
        ] + [
            ("memory", item.business_id, item.source_hash, item.version)
            for item in self.repo.list_private_memories(story.id, status="approved")
        ]
        raw = json.dumps(sorted(approved), ensure_ascii=False, separators=(",", ":"))
        story.memory_ledger_hash = hashlib.sha256(raw.encode()).hexdigest()
        story.memory_review_status = "reviewed"

    def refresh_ledger(self, story: Story, *, commit: bool = True) -> None:
        self._advance_ledger(story)
        if commit:
            self.repo.commit()

    @staticmethod
    def _event_fields() -> set[str]:
        return {
            "summary",
            "occurred_at_anchor_business_id",
            "presentation",
            "audience_disclosure",
        }

    @staticmethod
    def _memory_fields() -> set[str]:
        return {
            "content",
            "belief",
            "belief_confidence",
            "salience",
            "occurred_at_anchor_business_id",
            "learned_at_anchor_business_id",
            "effective_from_anchor_business_id",
            "invalidated_at_anchor_business_id",
        }
