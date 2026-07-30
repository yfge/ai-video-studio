"""Build the frozen typed contract for one gated novel chapter."""

from app.core.exceptions import ServiceError
from app.services.story.story_novel_plan_versions import is_v3_plan

from .extraction_bindings import (
    bound_knowledge_grant_keys,
    knowledge_character_bindings,
)


def novel_candidate_contract(repo, story, request, characters):
    if request.source_scope != "novel_chapter" or not hasattr(repo, "novel_chapter"):
        return False, None, {}, []
    chapter = repo.novel_chapter(story, request.source_artifact_business_id or "")
    if chapter and is_v3_plan(chapter.novel_export.generation_plan):
        raise ServiceError("v3 小说章节候选由已验证 proof spans 确定性生成")
    if (
        not chapter
        or (chapter.novel_export.generation_plan or {}).get("schema")
        != "story_novel_generation_plan.v2"
    ):
        return False, None, {}, []
    entry = ((chapter.novel_export.continuity_ledger or {}).get("chapters") or {}).get(
        str(chapter.position)
    ) or {}
    delta = entry.get("state_delta") or {}
    event_ids = list(delta.get("occurred_event_ids") or [])
    event_evidence = {
        event_id: str((delta.get("evidence") or {}).get(event_id) or "")
        for event_id in event_ids
    }
    if any(not quote for quote in event_evidence.values()):
        raise ServiceError("记忆候选提取失败：typed event 缺少逐字来源证据")
    bindings = knowledge_character_bindings(
        (chapter.novel_export.generation_plan or {}).get("canon") or {},
        delta,
        characters,
    )
    keys = [list(item) for item in sorted(bound_knowledge_grant_keys(bindings))]
    return True, bindings, event_evidence, keys
