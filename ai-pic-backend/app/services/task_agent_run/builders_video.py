from __future__ import annotations

from typing import Any, Dict

from app.repositories.script_repository import ScriptRepository
from app.repositories.video_generation_task_repository import (
    VideoGenerationTaskRepository,
)
from app.services.task_agent_run.timeline_refs import domain_ref_for_script
from app.services.task_agent_run.utils import (
    loads_task_parameters,
    maybe_int,
    split_provider_model,
)


def build_video_generation_agent_run(db, task, *, user_id: int) -> Dict[str, Any]:
    params = loads_task_parameters(getattr(task, "parameters", None))
    script_id = maybe_int(params.get("script_id"))

    subtasks = sorted(
        (
            item
            for item in VideoGenerationTaskRepository(db).list_by_task_id(task.id)
            if item.user_id == user_id
        ),
        key=lambda item: (item.frame_index or 0, item.id),
    )
    if not subtasks:
        return {}

    providers = sorted({t.provider for t in subtasks if getattr(t, "provider", None)})
    models = sorted({t.model for t in subtasks if getattr(t, "model", None)})
    provider_used = providers[0] if len(providers) == 1 else "mixed"
    model_used = models[0] if len(models) == 1 else None

    override_prompt = params.get("prompt")
    requested_model = params.get("model")
    requested_provider, requested_model_id = split_provider_model(requested_model)

    status_counts: Dict[str, int] = {}
    frame_indexes: list[int] = []
    for item in subtasks:
        status = str(getattr(item, "status", "") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
        if item.frame_index is not None:
            frame_indexes.append(int(item.frame_index))

    domain_ref: Dict[str, Any] = {}
    if script_id is not None:
        script = ScriptRepository(db).get_with_relations(
            script_id=script_id,
            user_id=user_id,
        )
        if script:
            domain_ref = domain_ref_for_script(db, script)
    timeline_rework = params.get("timeline_rework_by_frame")
    clip_ids = sorted(
        {
            str(context.get("clip_id")).strip()
            for context in (
                timeline_rework.values() if isinstance(timeline_rework, dict) else []
            )
            if isinstance(context, dict) and context.get("clip_id")
        }
    )
    explicit_timeline = {
        key: params.get(key)
        for key in ("timeline_id", "timeline_version")
        if params.get(key) is not None
    }
    clip_ref: Dict[str, Any] = {"clip_ids": clip_ids} if clip_ids else {}
    if len(clip_ids) == 1:
        clip_ref["clip_id"] = clip_ids[0]

    return {
        "generation_method": "video_generation",
        "provider_used": provider_used,
        "model_used": model_used or requested_model_id,
        "prompt": (
            override_prompt
            if isinstance(override_prompt, str)
            else getattr(task, "prompt", None)
        ),
        "requested_provider": requested_provider,
        "requested_model": requested_model_id,
        "result_ref": {
            "script_id": script_id,
            "frame_indexes": sorted({i for i in frame_indexes}),
            "video_task_count": len(subtasks),
            "status_counts": status_counts,
            **domain_ref,
            **explicit_timeline,
            **clip_ref,
        },
        "providers": providers,
        "models": models,
    }
