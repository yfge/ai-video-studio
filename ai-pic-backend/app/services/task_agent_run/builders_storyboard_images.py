from __future__ import annotations

from typing import Any, Dict

from app.repositories.script_repository import ScriptRepository
from app.services.task_agent_run.timeline_refs import domain_ref_for_script
from app.services.task_agent_run.utils import (
    loads_task_parameters,
    maybe_int,
    parse_result_id,
    split_provider_model,
)


def build_storyboard_image_agent_run(db, task, *, user_id: int) -> Dict[str, Any]:
    params = loads_task_parameters(getattr(task, "parameters", None))
    script_id = _resolve_script_id(task)
    if script_id is None:
        return {}

    script = ScriptRepository(db).get_with_relations(
        script_id=script_id,
        user_id=user_id,
    )
    if not script:
        return {}

    requested_model = params.get("model")
    provider_used, model_used = split_provider_model(requested_model)
    if (
        model_used is None
        and isinstance(requested_model, str)
        and requested_model.strip()
    ):
        model_used = requested_model.strip()

    frames = params.get("frames") or []
    if not isinstance(frames, list):
        frames = []

    prompt_override = params.get("prompt")
    payload: Dict[str, Any] = {
        "generation_method": "storyboard_image",
        "provider_used": provider_used,
        "model_used": model_used,
        "prompt": (
            prompt_override
            if isinstance(prompt_override, str)
            else getattr(task, "prompt", None)
        ),
        "result_ref": {
            "script_id": getattr(script, "id", None),
            "script_business_id": getattr(script, "business_id", None),
            "episode_id": getattr(script, "episode_id", None),
            "episode_business_id": getattr(script, "episode_business_id", None),
            "frame_indexes": frames,
            **domain_ref_for_script(db, script),
        },
    }
    keyframe_mode = params.get("keyframe_mode")
    if isinstance(keyframe_mode, str) and keyframe_mode.strip():
        payload["keyframe_mode"] = keyframe_mode
    generation_profile = params.get("generation_profile")
    if isinstance(generation_profile, str) and generation_profile.strip():
        payload["generation_profile"] = generation_profile
    return payload


def _resolve_script_id(task) -> int | None:
    script_id_str = parse_result_id(
        getattr(task, "result_file_path", None), prefix="script"
    )
    if script_id_str:
        token = script_id_str.split(":", 1)[0]
        script_id = maybe_int(token)
        if script_id is not None:
            return script_id

    params = loads_task_parameters(getattr(task, "parameters", None))
    return maybe_int(params.get("script_id"))
