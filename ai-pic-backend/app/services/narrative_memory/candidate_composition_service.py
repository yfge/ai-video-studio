"""Human-directed split and merge operations for narrative candidates."""

from copy import deepcopy

from app.core.exceptions import ConflictError, ValidationError
from app.models.script import Story
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.services.narrative_memory.access import require_version
from app.services.narrative_memory.candidate_service import CandidateService


class CandidateCompositionService:
    def __init__(self, repo: NarrativeMemoryRepository):
        self.repo = repo
        self.candidates = CandidateService(repo)

    def split(
        self,
        story: Story,
        business_id: str,
        *,
        expected_version: int,
        contents: list[str],
        user_id: int,
    ):
        kind, entity = self.candidates._candidate(story, business_id)
        require_version(entity, expected_version)
        self._require_composable(entity)
        clean = [value.strip() for value in contents if value.strip()]
        if len(clean) < 2:
            raise ValidationError("拆分至少需要两条非空内容")
        created = [
            self._clone_candidate(
                story,
                kind,
                entity,
                content,
                user_id,
                evidence={"split_from": entity.business_id, "part": index},
            )
            for index, content in enumerate(clean, start=1)
        ]
        entity.status = "superseded"
        entity.version = int(entity.version or 1) + 1
        self.repo.commit()
        return kind, created

    def merge(
        self,
        story: Story,
        *,
        business_ids: list[str],
        expected_versions: dict[str, int],
        merged_content: str | None,
        user_id: int,
    ):
        unique = list(dict.fromkeys(business_ids))
        if len(unique) < 2:
            raise ValidationError("合并至少需要两个不同候选")
        rows = [self.candidates._candidate(story, value) for value in unique]
        kinds = {kind for kind, _entity in rows}
        if len(kinds) != 1:
            raise ValidationError("客观事件与角色记忆不能合并")
        for _kind, entity in rows:
            require_version(entity, expected_versions.get(entity.business_id, -1))
            self._require_composable(entity)
        kind = rows[0][0]
        entities = [entity for _kind, entity in rows]
        if (
            kind == "memory"
            and len({item.character_business_id for item in entities}) != 1
        ):
            raise ValidationError("只能合并同一角色的记忆")
        content = (
            merged_content or "；".join(self._content(kind, item) for item in entities)
        ).strip()
        created = self._clone_candidate(
            story,
            kind,
            entities[0],
            content,
            user_id,
            evidence={"merged_from": unique},
        )
        for entity in entities:
            entity.status = "superseded"
            entity.version = int(entity.version or 1) + 1
        self.repo.commit()
        return kind, created

    @staticmethod
    def _require_composable(entity) -> None:
        if entity.status not in {"candidate", "stale"}:
            raise ConflictError("只有候选或 stale 内容可以拆分/合并")

    def _clone_candidate(self, story, kind, source, content, user_id, *, evidence):
        if kind == "event":
            data = {
                "event_type": source.event_type,
                "summary": content,
                "participant_character_ids": source.participant_character_ids or [],
                "occurred_at_anchor_business_id": source.occurred_at_anchor_business_id,
                "presentation": source.presentation,
                "audience_disclosure": source.audience_disclosure,
                "source_artifact_type": source.source_artifact_type,
                "source_artifact_business_id": source.source_artifact_business_id,
                "source_version": source.source_version,
                "source_hash": source.source_hash,
                "candidate_evidence": self._evidence(source, evidence),
            }
            return self.candidates._create_event(story, data, user_id)
        data = {
            key: deepcopy(getattr(source, key))
            for key in (
                "character_business_id",
                "virtual_ip_business_id",
                "memory_type",
                "event_business_id",
                "belief",
                "belief_confidence",
                "perception",
                "emotional_impact",
                "salience",
                "occurred_at_anchor_business_id",
                "learned_at_anchor_business_id",
                "effective_from_anchor_business_id",
                "invalidated_at_anchor_business_id",
                "source_artifact_type",
                "source_artifact_business_id",
                "source_version",
                "source_hash",
            )
        }
        data["content"] = content
        data["candidate_evidence"] = self._evidence(source, evidence)
        return self.candidates._create_memory(story, data, user_id)

    @staticmethod
    def _content(kind: str, entity) -> str:
        return entity.summary if kind == "event" else entity.content

    @staticmethod
    def _evidence(source, addition: dict) -> dict:
        return {**deepcopy(source.candidate_evidence or {}), **addition}
