from __future__ import annotations

from typing import Any, Dict

from app.services.task_agent_run.utils import loads_task_parameters, maybe_int, split_provider_model


def build_video_generation_agent_run(db, task, *, user_id: int) -> Dict[str, Any]:
    from app.models.video_generation_task import VideoGenerationTask

    params = loads_task_parameters(getattr(task, "parameters", None))
    script_id = maybe_int(params.get("script_id"))

    subtasks = (
        db.query(VideoGenerationTask)
        .filter(
            VideoGenerationTask.task_id == task.id,
            VideoGenerationTask.user_id == user_id,
        )
        .order_by(VideoGenerationTask.frame_index.asc(), VideoGenerationTask.id.asc())
        .all()
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

    return {
        "generation_method": "video_generation",
        "provider_used": provider_used,
        "model_used": model_used or requested_model_id,
        "prompt": override_prompt if isinstance(override_prompt, str) else getattr(task, "prompt", None),
        "requested_provider": requested_provider,
        "requested_model": requested_model_id,
        "result_ref": {
            "script_id": script_id,
            "frame_indexes": sorted({i for i in frame_indexes}),
            "video_task_count": len(subtasks),
            "status_counts": status_counts,
        },
        "providers": providers,
        "models": models,
    }

