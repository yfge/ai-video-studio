"""Small runtime helpers shared by v3 chapter stages."""

from app.services.narrative_memory.candidate_verification import (
    complete_novel_candidate_set,
)

from .story_novel_chapter_service import source_candidates


def candidate_checkpoint_ready(service, revision, chapter, entry) -> bool:
    if entry.get("extraction_status") != "ready":
        return False
    events, memories = source_candidates(service.db, revision, chapter)
    return bool(
        entry.get("event_ids") == [item.business_id for item in events]
        and entry.get("memory_ids") == [item.business_id for item in memories]
        and complete_novel_candidate_set(entry, events, memories)
    )


def update_progress(service, task, position, revision, stage):
    labels = {
        "chapter_planning": "章前规划",
        "prose": "正文分块生成",
        "audit": "状态与证据审计",
        "local_repair": "局部 block 返修",
        "memory_ready": "Narrative 落账",
    }
    task.description = f"第 {position}/{revision.chapter_count} 章：{labels[stage]}"
    service.db.commit()
