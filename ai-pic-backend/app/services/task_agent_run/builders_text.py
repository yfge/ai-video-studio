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
    return payload
