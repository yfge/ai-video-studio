"""Human-only promotion of story memories into shared character memory."""

import hashlib
from datetime import datetime

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.user import User
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.repositories.narrative_promotion_repository import NarrativePromotionRepository
from app.services.narrative_memory.access import require_version


class PromotionService:
    def __init__(self, memory_repo, promotion_repo):
        self.memory_repo: NarrativeMemoryRepository = memory_repo
        self.promotion_repo: NarrativePromotionRepository = promotion_repo

    def create_candidate(
        self,
        primary_memory_business_id: str,
        source_memory_ids: list[str],
        candidate_content: str,
        user: User,
    ):
        primary = self.memory_repo.get_owned_private_memory(
            primary_memory_business_id, user
        )
        if not primary or not primary.story_id:
            raise NotFoundError("角色私有记忆", primary_memory_business_id)
        requested = list(
            dict.fromkeys([primary_memory_business_id, *source_memory_ids])
        )
        sources = self.promotion_repo.get_source_memories(primary.story_id, requested)
        if len(sources) != len(requested) or any(
            item.status != "approved" for item in sources
        ):
            raise ValidationError("公共记忆候选只能引用当前 Story 已审批的私有记忆")
        if any(item.virtual_ip_id != primary.virtual_ip_id for item in sources):
            raise ValidationError("一次公共记忆提升只能属于同一 Virtual IP")
        if not self.promotion_repo.get_owned_virtual_ip(
            primary.virtual_ip_business_id, user
        ):
            raise NotFoundError.virtual_ip(primary.virtual_ip_business_id)
        promotion = self.promotion_repo.create_promotion(
            source_story_id=primary.story_id,
            source_story_business_id=primary.story_business_id,
            source_memory_ids=requested,
            target_virtual_ip_id=primary.virtual_ip_id,
            target_virtual_ip_business_id=primary.virtual_ip_business_id,
            canon_branch_id=primary.canon_branch_id,
            candidate_content=candidate_content,
            status="pending",
            created_by=user.id,
        )
        self.promotion_repo.commit()
        self.promotion_repo.refresh(promotion)
        return promotion

    def update(self, business_id: str, *, expected_version: int, user: User, **updates):
        promotion = self._owned_promotion(business_id, user)
        require_version(promotion, expected_version)
        if promotion.status != "pending":
            raise ConflictError("已审核的公共记忆候选不可编辑")
        for field, value in updates.items():
            if value is not None:
                setattr(promotion, field, value)
        promotion.version += 1
        self.promotion_repo.commit()
        self.promotion_repo.refresh(promotion)
        return promotion

    def review(
        self,
        business_id: str,
        *,
        expected_version: int,
        approved: bool,
        reason: str | None,
        user: User,
    ):
        promotion = self._owned_promotion(business_id, user)
        require_version(promotion, expected_version)
        if promotion.status != "pending":
            raise ConflictError("公共记忆候选已被审核")
        promotion.decision_reason = reason
        promotion.version += 1
        if approved:
            shared = self._publish(promotion, user.id)
            promotion.status = "approved"
            promotion.approved_by = user.id
            promotion.approved_at = datetime.utcnow()
            self.promotion_repo.flush()
            promotion.result_shared_memory_business_id = shared.business_id
        else:
            promotion.status = "rejected"
        self.promotion_repo.commit()
        self.promotion_repo.refresh(promotion)
        return promotion

    def clone_shared(
        self,
        virtual_ip_business_id: str,
        memory_business_id: str,
        *,
        content: str | None,
        user: User,
    ):
        target, memory = self._owned_shared(
            virtual_ip_business_id, memory_business_id, user
        )
        return self._copy_shared(
            target, memory, content or memory.content, user.id, supersede=False
        )

    def supersede_shared(
        self,
        virtual_ip_business_id: str,
        memory_business_id: str,
        *,
        expected_version: int,
        content: str,
        user: User,
    ):
        target, memory = self._owned_shared(
            virtual_ip_business_id, memory_business_id, user
        )
        require_version(memory, expected_version)
        if memory.status != "approved":
            raise ConflictError("只有当前已审批公共记忆可以被替代")
        result = self._copy_shared(
            target, memory, content, user.id, supersede=True, commit=False
        )
        memory.status = "superseded"
        self.promotion_repo.commit()
        self.promotion_repo.refresh(result)
        return result

    def _publish(self, promotion, user_id: int):
        return self.promotion_repo.create_shared_memory(
            **self._shared_data(
                virtual_ip_id=promotion.target_virtual_ip_id,
                virtual_ip_business_id=promotion.target_virtual_ip_business_id,
                canon_branch_id=promotion.canon_branch_id,
                content=promotion.candidate_content,
                source_type="memory_promotion",
                source_id=promotion.business_id,
                source_version=promotion.version,
                source_ids=promotion.source_memory_ids,
                user_id=user_id,
            )
        )

    def _copy_shared(self, target, memory, content, user_id, *, supersede, commit=True):
        data = self._shared_data(
            virtual_ip_id=target.id,
            virtual_ip_business_id=target.business_id,
            canon_branch_id=memory.canon_branch_id,
            content=content,
            source_type="shared_memory_revision",
            source_id=memory.business_id,
            source_version=memory.version,
            source_ids=[memory.business_id],
            user_id=user_id,
        )
        data.update(
            memory_type=memory.memory_type,
            belief=memory.belief,
            belief_confidence=memory.belief_confidence,
            perception=memory.perception,
            emotional_impact=memory.emotional_impact,
            salience=memory.salience,
            supersedes_business_id=memory.business_id if supersede else None,
        )
        copied = self.promotion_repo.create_shared_memory(**data)
        if commit:
            self.promotion_repo.commit()
            self.promotion_repo.refresh(copied)
        return copied

    def _shared_data(self, **values) -> dict:
        source_ids = values.pop("source_ids")
        content = values["content"]
        virtual_ip_id = values["virtual_ip_id"]
        return {
            "story_id": None,
            "story_business_id": None,
            "character_business_id": None,
            "scope": "character_shared",
            "memory_type": "remembered",
            "learned_at_anchor_business_id": "shared_baseline",
            "effective_from_anchor_business_id": "shared_baseline",
            "status": "approved",
            "source_artifact_type": values.pop("source_type"),
            "source_artifact_business_id": values.pop("source_id"),
            "source_hash": self._source_hash(source_ids, content),
            "candidate_evidence": {"source_memory_ids": source_ids},
            "version": self.promotion_repo.next_shared_version(
                virtual_ip_id, values["canon_branch_id"]
            ),
            "created_by": values["user_id"],
            "approved_by": values.pop("user_id"),
            "approved_at": datetime.utcnow(),
            **values,
        }

    def _owned_promotion(self, business_id: str, user: User):
        promotion = self.promotion_repo.get_promotion(business_id)
        if not promotion or not self.promotion_repo.get_owned_virtual_ip(
            promotion.target_virtual_ip_business_id, user
        ):
            raise NotFoundError("公共记忆候选", business_id)
        return promotion

    def _owned_shared(self, virtual_ip_business_id, memory_business_id, user):
        target = self.promotion_repo.get_owned_virtual_ip(virtual_ip_business_id, user)
        if not target:
            raise NotFoundError.virtual_ip(virtual_ip_business_id)
        memory = self.promotion_repo.get_shared_memory(target.id, memory_business_id)
        if not memory:
            raise NotFoundError("公共记忆", memory_business_id)
        return target, memory

    @staticmethod
    def _source_hash(source_ids: list[str], content: str) -> str:
        value = "|".join(sorted(source_ids)) + "|" + content
        return hashlib.sha256(value.encode()).hexdigest()
