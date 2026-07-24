import json

from app.core.exceptions import ConflictError, ServiceError
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.schemas.narrative_extraction import (
    NarrativeExtractionEnvelope,
    NarrativeExtractionRequest,
)
from app.services.ai.structured_output import generate_with_repair
from app.services.ai_service import ai_service
from app.services.narrative_memory.candidate_service import CandidateService
from app.services.narrative_memory.evidence_repair import (
    repair_invalid_extraction_evidence,
)
from app.services.narrative_memory.extraction_candidates import (
    build_candidate_payload,
    knowledge_character_bindings,
)
from app.services.narrative_memory.extraction_evidence import (
    extraction_evidence_errors,
    normalize_extraction_evidence,
)
from app.services.narrative_memory.extraction_prompt import build_extraction_prompt
from app.services.narrative_memory.novel_chapter_gate import require_gated_novel_chapter
from app.services.narrative_memory.source_hash import (
    artifact_hash,
    novel_chapter_source_hash,
)


class NarrativeExtractionService:
    def __init__(self, repo: NarrativeMemoryRepository):
        self.repo = repo

    async def extract(
        self,
        story,
        request: NarrativeExtractionRequest,
        user,
        *,
        commit: bool = True,
        before_ingest=None,
    ):
        anchors, source_text = self._source(
            story,
            request.source_scope,
            request.source_artifact_business_id,
        )
        characters = [
            {
                "character_business_id": item.business_id,
                "virtual_ip_business_id": item.virtual_ip.business_id,
                "name": item.display_name,
            }
            for item in self.repo.list_story_characters(story.id)
            if item.virtual_ip
        ]
        strict, memory_bindings, event_evidence = self._candidate_contract(
            story, request, characters
        )
        self.repo.commit()
        manager = ai_service.ai_manager
        if not manager:
            raise ServiceError("当前没有可用的文本模型提供商")
        prompt = self._prompt(
            source_text,
            characters,
            anchors,
            (
                {
                    "event_evidence": event_evidence,
                    "required_memory_grants": memory_bindings or {},
                }
                if strict
                else None
            ),
        )
        result = await generate_with_repair(
            ai_manager=manager,
            base_prompt=prompt,
            model=request.model,
            prefer_provider=None,
            temperature=0.2,
            schema_name="narrative_memory_delta",
            schema=NarrativeExtractionEnvelope.model_json_schema(),
            system_prompt="你是严格的叙事事实与角色认知提取器，只返回 JSON。",
            pydantic_model=NarrativeExtractionEnvelope,
            max_repairs=1,
        )
        normalized = result.get("normalized")
        errors = result.get("validation_errors") or []
        if normalized:
            evidence_errors = extraction_evidence_errors(normalized, source_text)
            if evidence_errors:
                errors = evidence_errors
                normalized = await repair_invalid_extraction_evidence(
                    manager,
                    {
                        "raw_json": normalized,
                        "validation_errors": evidence_errors,
                    },
                    source_text=source_text,
                    model=request.model,
                )
        elif errors and all(
            item.get("type") == "value_error.source_evidence" for item in errors
        ):
            normalized = await repair_invalid_extraction_evidence(
                manager,
                {"raw_json": result.get("raw_json"), "validation_errors": errors},
                source_text=source_text,
                model=request.model,
            )
        if normalized is None:
            detail = (errors[0] if errors else {}).get("msg") or "未返回有效结构"
            raise ServiceError(f"记忆候选提取失败：{detail}")
        normalize_extraction_evidence(normalized, source_text)
        payload = build_candidate_payload(
            normalized,
            anchors,
            characters,
            strict=strict,
            memory_character_bindings=memory_bindings,
            occurred_event_evidence=event_evidence,
        )
        if before_ingest is not None:
            before_ingest()
        return CandidateService(self.repo).ingest(story, payload, user, commit=commit)

    def _candidate_contract(self, story, request, characters):
        if request.source_scope != "novel_chapter" or not hasattr(
            self.repo, "novel_chapter"
        ):
            return False, None, {}
        chapter = self.repo.novel_chapter(
            story, request.source_artifact_business_id or ""
        )
        if (
            not chapter
            or (chapter.novel_export.generation_plan or {}).get("schema")
            != "story_novel_generation_plan.v2"
        ):
            return False, None, {}
        entry = (
            (chapter.novel_export.continuity_ledger or {}).get("chapters") or {}
        ).get(str(chapter.position)) or {}
        delta = entry.get("state_delta") or {}
        event_ids = list(delta.get("occurred_event_ids") or [])
        event_evidence = {
            event_id: str((delta.get("evidence") or {}).get(event_id) or "")
            for event_id in event_ids
        }
        if any(not quote for quote in event_evidence.values()):
            raise ServiceError("记忆候选提取失败：typed event 缺少逐字来源证据")
        return (
            True,
            knowledge_character_bindings(
                (chapter.novel_export.generation_plan or {}).get("canon") or {},
                delta,
                characters,
            ),
            event_evidence,
        )

    def _source(self, story, scope: str, source_artifact_business_id: str | None):
        if scope == "novel_chapter":
            chapter = self.repo.novel_chapter(story, source_artifact_business_id or "")
            if not chapter:
                raise ConflictError("小说章节不存在或不属于当前 Story")
            require_gated_novel_chapter(self.repo.session, chapter)
            anchor = self._existing_or_chapter_anchor(story, chapter)
            self.repo.commit()
            return [anchor], f"{chapter.title}\n{chapter.content_text}"
        if scope == "canonical_novel":
            revision = self.repo.canonical_novel(story)
            if not revision or revision.lifecycle_status != "approved":
                raise ConflictError("尚无已审批 canonical 小说可提取")
            anchors = []
            parts = []
            existing = {
                item.source_artifact_business_id: item
                for item in self.repo.list_anchors(story.id)
            }
            for chapter in revision.chapters:
                anchor = existing.get(chapter.business_id) or self._chapter_anchor(
                    story, chapter
                )
                anchors.append(anchor)
                parts.append(
                    f"[{anchor.business_id}] {chapter.title}\n{chapter.content_text}"
                )
            self.repo.commit()
            return anchors, "\n\n".join(parts)
        seed = story.story_seed or {}
        source_hash = artifact_hash(seed)
        existing = next(
            (
                item
                for item in self.repo.list_anchors(story.id)
                if item.source_artifact_type == "story_seed"
                and item.source_hash == source_hash
            ),
            None,
        )
        anchor = existing or self.repo.create_anchor(
            story_id=story.id,
            story_business_id=story.business_id,
            canon_branch_id=story.canon_branch_id or "main",
            anchor_type="chapter",
            narrative_sequence=0,
            source_artifact_type="story_seed",
            source_artifact_business_id=story.business_id,
            source_version=story.story_seed_version or 1,
            source_hash=source_hash,
        )
        self.repo.commit()
        return [anchor], json.dumps(seed, ensure_ascii=False)

    def _existing_or_chapter_anchor(self, story, chapter):
        source_hash = novel_chapter_source_hash(chapter)
        return next(
            (
                item
                for item in self.repo.list_anchors(story.id)
                if item.source_artifact_business_id == chapter.business_id
                and item.source_hash == source_hash
            ),
            None,
        ) or self._chapter_anchor(story, chapter)

    def _chapter_anchor(self, story, chapter):
        return self.repo.create_anchor(
            story_id=story.id,
            story_business_id=story.business_id,
            canon_branch_id=story.canon_branch_id or "main",
            anchor_type="chapter",
            chapter_business_id=chapter.business_id,
            narrative_sequence=chapter.position * 1000,
            source_artifact_type="novel_chapter",
            source_artifact_business_id=chapter.business_id,
            source_version=1,
            source_hash=novel_chapter_source_hash(chapter),
        )

    @staticmethod
    def _prompt(source_text, characters, anchors, contract=None) -> str:
        return build_extraction_prompt(source_text, characters, anchors, contract)
