from __future__ import annotations

from typing import Any, Dict

from app.services.task_agent_run.utils import (
    loads_task_parameters,
    split_provider_model,
)


def build_story_novel_export_agent_run(db, task, *, user_id: int) -> Dict[str, Any]:
    from app.repositories.story_novel_repository import StoryNovelRepository

    export_row = StoryNovelRepository(db).revision_for_task_or_target(
        task.id,
        getattr(task, "target_business_id", None),
        user_id,
    )
    params = loads_task_parameters(getattr(task, "parameters", None))
    model_value = (
        getattr(export_row, "model", None) if export_row else params.get("model")
    )
    provider_used, model_used = split_provider_model(model_value)

    story_business_id = None
    story_id = None
    if export_row:
        story_business_id = export_row.story_business_id
        story_id = export_row.story_id

    payload: Dict[str, Any] = {
        "generation_method": "story_novel_export",
        "provider_used": provider_used,
        "model_used": model_used,
        "prompt": getattr(task, "prompt", None),
        "result_ref": {
            "story_id": story_id,
            "story_business_id": story_business_id,
            "export_id": getattr(export_row, "id", None) if export_row else None,
            "revision_business_id": (
                getattr(export_row, "business_id", None) if export_row else None
            ),
            "file_relative_path": (
                getattr(export_row, "file_relative_path", None) if export_row else None
            ),
        },
    }
    if export_row:
        payload["temperature"] = getattr(export_row, "temperature", None)
        payload["target_words"] = getattr(export_row, "target_words", None)
        payload["total_words"] = getattr(export_row, "total_words", None)
        payload["chapter_count"] = getattr(export_row, "chapter_count", None)
        payload["content_hash"] = getattr(export_row, "content_hash", None)
        payload["lifecycle_status"] = getattr(export_row, "lifecycle_status", None)
        plan = getattr(export_row, "generation_plan", None) or {}
        ledger = getattr(export_row, "continuity_ledger", None) or {}
        payload["generation_plan_status"] = plan.get("status")
        payload["chapter_context_evidence"] = [
            {
                "position": int(position),
                "body_hash": entry.get("body_hash"),
                "source_hash": entry.get("source_hash"),
                "context_hash": entry.get("context_hash"),
                "context_evidence": entry.get("context_evidence"),
                "event_ids": entry.get("event_ids") or [],
                "memory_ids": entry.get("memory_ids") or [],
                "extraction_status": entry.get("extraction_status"),
            }
            for position, entry in sorted(
                (ledger.get("chapters") or {}).items(), key=lambda item: int(item[0])
            )
        ]
    return payload
