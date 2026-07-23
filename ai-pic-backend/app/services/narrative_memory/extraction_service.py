"""Explicit paid-operation boundary for extracting candidate memory deltas."""

import json

from app.core.exceptions import ConflictError, ServiceError
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.schemas.narrative_extraction import (
    NarrativeExtractionEnvelope,
    NarrativeExtractionRequest,
)
from app.schemas.narrative_memory import (
    CandidateDeltaCreate,
    CharacterMemoryCandidateCreate,
    NarrativeEventCandidateCreate,
)
from app.services.ai.structured_output import generate_with_repair
from app.services.ai_service import ai_service
from app.services.narrative_memory.candidate_service import CandidateService
from app.services.narrative_memory.source_hash import (
    artifact_hash,
    novel_chapter_source_hash,
)


class NarrativeExtractionService:
    def __init__(self, repo: NarrativeMemoryRepository):
        self.repo = repo

    async def extract(self, story, request: NarrativeExtractionRequest, user):
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
        manager = ai_service.ai_manager
        if not manager:
            raise ServiceError("当前没有可用的文本模型提供商")
        prompt = self._prompt(source_text, characters, anchors)
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
        if not normalized:
            raise ServiceError("记忆候选提取失败：模型未返回有效结构")
        payload = self._candidate_payload(normalized, anchors)
        return CandidateService(self.repo).ingest(story, payload, user)

    def _source(self, story, scope: str, source_artifact_business_id: str | None):
        if scope == "novel_chapter":
            chapter = self.repo.novel_chapter(story, source_artifact_business_id or "")
            if not chapter:
                raise ConflictError("小说章节不存在或不属于当前 Story")
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

    def _candidate_payload(
        self, normalized: dict, anchors: list
    ) -> CandidateDeltaCreate:
        by_id = {item.business_id: item for item in anchors}
        fallback = anchors[0]
        events = []
        for raw in normalized.get("events") or []:
            item = dict(raw)
            anchor = by_id.get(item.get("occurred_at_anchor_business_id")) or fallback
            item["occurred_at_anchor_business_id"] = anchor.business_id
            events.append(
                NarrativeEventCandidateCreate(
                    **item,
                    source_artifact_type=anchor.source_artifact_type,
                    source_artifact_business_id=anchor.source_artifact_business_id,
                    source_version=anchor.source_version,
                    source_hash=anchor.source_hash,
                )
            )
        memories = []
        for raw in normalized.get("memories") or []:
            item = dict(raw)
            growth_delta = item.pop("growth_delta", None)
            learned = by_id.get(item.get("learned_at_anchor_business_id")) or fallback
            item["learned_at_anchor_business_id"] = learned.business_id
            item["effective_from_anchor_business_id"] = (
                by_id.get(item.get("effective_from_anchor_business_id")) or learned
            ).business_id
            if item.get("occurred_at_anchor_business_id"):
                item["occurred_at_anchor_business_id"] = (
                    by_id.get(item["occurred_at_anchor_business_id"]) or learned
                ).business_id
            if item.get("invalidated_at_anchor_business_id"):
                item["invalidated_at_anchor_business_id"] = (
                    by_id.get(item["invalidated_at_anchor_business_id"]) or learned
                ).business_id
            memories.append(
                CharacterMemoryCandidateCreate(
                    **item,
                    source_artifact_type=learned.source_artifact_type,
                    source_artifact_business_id=learned.source_artifact_business_id,
                    source_version=learned.source_version,
                    source_hash=learned.source_hash,
                    candidate_evidence=(
                        {"growth_delta": growth_delta} if growth_delta else None
                    ),
                )
            )
        return CandidateDeltaCreate(events=events, memories=memories)

    @staticmethod
    def _prompt(source_text, characters, anchors) -> str:
        return f"""从来源正文提取客观事件和每个角色的主观记忆候选。
角色白名单：{json.dumps(characters, ensure_ascii=False)}
可用锚点：{json.dumps([{'business_id': a.business_id, 'source': a.source_artifact_business_id} for a in anchors], ensure_ascii=False)}
严格区分：客观事件、角色获知/信念、观众显隐。离场发生用 presentation=offscreen；不要把潜台词写成长期记忆。
只保留会影响后续连续性、知情边界、关系、能力或世界规则的增量；忽略重复信息、气氛描写、普通动作和逐句对话。
硬性控制输出规模：events 最多 8 条，memories 总计最多 6 条；summary、content、belief、perception 各字段都用一句简洁中文。
角色没有获得新的长期认知时不要为其创建 memory；允许 events 或 memories 为空数组。
只输出严格 JSON，字段和值必须遵守以下合同，不得自创别名或枚举：
{{"events":[{{"event_type":"action|reveal|relationship|state_change|world_fact","summary":"客观事实","participant_character_ids":["角色 business_id"],"occurred_at_anchor_business_id":"锚点 business_id","presentation":"on_screen|offscreen|withheld","audience_disclosure":"hidden|hinted|partial|revealed"}}],"memories":[{{"character_business_id":"角色 business_id","virtual_ip_business_id":"虚拟IP business_id","memory_type":"witnessed|heard|inferred|dreamed|misled|remembered","content":"角色长期记住的内容","belief":"可选信念","belief_confidence":0.8,"perception":"可选感知","emotional_impact":["情绪"],"salience":0.8,"occurred_at_anchor_business_id":"锚点 business_id","learned_at_anchor_business_id":"锚点 business_id","effective_from_anchor_business_id":"锚点 business_id","invalidated_at_anchor_business_id":null,"growth_delta":{{}}}}]}}
participant_character_ids、character_business_id 只能取角色白名单中的 character_business_id；锚点字段只能取可用锚点 business_id。
来源正文：\n{source_text}"""
