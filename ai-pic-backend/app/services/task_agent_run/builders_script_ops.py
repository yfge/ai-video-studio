from __future__ import annotations

from typing import Any, Dict

from app.repositories.script_repository import ScriptRepository
from app.services.task_agent_run.builders_storyboard_images import (
    build_storyboard_image_agent_run,
)
from app.services.task_agent_run.timeline_refs import domain_ref_for_script
from app.services.task_agent_run.utils import (
    loads_task_parameters,
    maybe_int,
    parse_result_id,
    safe_dict,
)

__all__ = [
    "build_dialogue_audio_agent_run",
    "build_storyboard_from_audio_timeline_agent_run",
    "build_storyboard_generation_agent_run",
    "build_storyboard_image_agent_run",
    "build_timeline_generation_agent_run",
    "build_timeline_pipeline_agent_run",
]


def _load_script_owned(db, *, script_id: int, user_id: int):
    return ScriptRepository(db).get_with_relations(script_id=script_id, user_id=user_id)


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


def build_dialogue_audio_agent_run(db, task, *, user_id: int) -> Dict[str, Any]:
    script_id = _resolve_script_id(task)
    if script_id is None:
        return {}

    script = _load_script_owned(db, script_id=script_id, user_id=user_id)
    if not script:
        return {}

    params = loads_task_parameters(getattr(task, "parameters", None))
    tts_model = params.get("tts_model") or "speech-2.6-hd"
    timing_model = params.get("timing_model")

    scene_numbers = params.get("scene_numbers") or []
    if not isinstance(scene_numbers, list):
        scene_numbers = []

    payload: Dict[str, Any] = {
        "generation_method": "dialogue_audio",
        "provider_used": "minimax",
        "model_used": str(tts_model),
        "timing_model": timing_model,
        "use_duration_control": bool(params.get("use_duration_control", False)),
        "prompt": getattr(task, "prompt", None),
        "result_ref": {
            "script_id": getattr(script, "id", None),
            "script_business_id": getattr(script, "business_id", None),
            "episode_id": getattr(script, "episode_id", None),
            "episode_business_id": getattr(script, "episode_business_id", None),
            "scene_numbers": scene_numbers,
            **domain_ref_for_script(db, script),
        },
    }

    overwrite_audio = params.get("overwrite_audio")
    if overwrite_audio is not None:
        payload["overwrite_audio"] = bool(overwrite_audio)
    return payload


def build_timeline_generation_agent_run(db, task, *, user_id: int) -> Dict[str, Any]:
    script_id = _resolve_script_id(task)
    if script_id is None:
        return {}

    script = _load_script_owned(db, script_id=script_id, user_id=user_id)
    if not script:
        return {}

    episode = getattr(script, "episode", None)
    timeline_meta = {}
    if episode and isinstance(getattr(episode, "extra_metadata", None), dict):
        timeline_meta = safe_dict(episode.extra_metadata.get("audio_timeline"))

    audio_payload = safe_dict(timeline_meta.get("episode_audio"))
    version = audio_payload.get("version")
    domain_ref = domain_ref_for_script(db, script)

    return {
        "generation_method": "audio_timeline",
        "provider_used": "pipeline",
        "prompt": getattr(task, "prompt", None),
        "result_ref": {
            "script_id": getattr(script, "id", None),
            "script_business_id": getattr(script, "business_id", None),
            "episode_id": getattr(script, "episode_id", None),
            "episode_business_id": getattr(script, "episode_business_id", None),
            "audio_timeline_version": version,
            **domain_ref,
        },
    }


def build_storyboard_generation_agent_run(db, task, *, user_id: int) -> Dict[str, Any]:
    script_id = _resolve_script_id(task)
    if script_id is None:
        return {}

    script = _load_script_owned(db, script_id=script_id, user_id=user_id)
    if not script:
        return {}

    meta = {}
    storyboard = {}
    if isinstance(getattr(script, "extra_metadata", None), dict):
        storyboard = safe_dict(script.extra_metadata.get("storyboard"))
        meta = safe_dict(storyboard.get("meta"))
    frames = storyboard.get("frames")
    plan = storyboard.get("plan")

    payload: Dict[str, Any] = {
        "generation_method": meta.get("generation_method"),
        "provider_used": meta.get("provider"),
        "model_used": meta.get("generation_model"),
        "usage": meta.get("usage"),
        "reasoning_trace": meta.get("reasoning_trace"),
        "prompt": getattr(task, "prompt", None),
        "result_ref": {
            "script_id": getattr(script, "id", None),
            "script_business_id": getattr(script, "business_id", None),
            "episode_id": getattr(script, "episode_id", None),
            "episode_business_id": getattr(script, "episode_business_id", None),
            "storyboard_version": getattr(script, "storyboard_version", None),
            "source_role": meta.get("source_role"),
            **domain_ref_for_script(db, script),
        },
    }
    if isinstance(frames, list):
        payload["frames"] = frames
    if isinstance(plan, dict):
        payload["plan"] = plan
    plan_fixes = meta.get("plan_fixes")
    if isinstance(plan_fixes, list):
        payload["plan_fixes"] = plan_fixes
    scene_scope = meta.get("scene_scope")
    if scene_scope is not None:
        payload["scene_scope"] = scene_scope
    return payload


def build_storyboard_from_audio_timeline_agent_run(
    db, task, *, user_id: int
) -> Dict[str, Any]:
    script_id = _resolve_script_id(task)
    if script_id is None:
        return {}

    script = _load_script_owned(db, script_id=script_id, user_id=user_id)
    if not script:
        return {}

    meta = {}
    if isinstance(getattr(script, "extra_metadata", None), dict):
        storyboard = safe_dict(script.extra_metadata.get("storyboard"))
        meta = safe_dict(storyboard.get("meta"))

    return {
        "generation_method": meta.get("generation_method") or "audio_timeline",
        "provider_used": "pipeline",
        "prompt": getattr(task, "prompt", None),
        "result_ref": {
            "script_id": getattr(script, "id", None),
            "script_business_id": getattr(script, "business_id", None),
            "episode_id": getattr(script, "episode_id", None),
            "episode_business_id": getattr(script, "episode_business_id", None),
            "audio_timeline_version": meta.get("audio_timeline_version"),
            "storyboard_version": getattr(script, "storyboard_version", None),
            "source_role": meta.get("source_role"),
            **domain_ref_for_script(db, script),
        },
    }


def build_timeline_pipeline_agent_run(db, task, *, user_id: int) -> Dict[str, Any]:
    script_id = _resolve_script_id(task)
    if script_id is None:
        return {}

    script = _load_script_owned(db, script_id=script_id, user_id=user_id)
    if not script:
        return {}

    params = loads_task_parameters(getattr(task, "parameters", None))
    tts_model = params.get("tts_model") or "speech-2.6-hd"
    timing_model = params.get("timing_model")

    episode = getattr(script, "episode", None)
    audio_version = None
    if episode and isinstance(getattr(episode, "extra_metadata", None), dict):
        timeline_meta = safe_dict(episode.extra_metadata.get("audio_timeline"))
        audio_payload = safe_dict(timeline_meta.get("episode_audio"))
        audio_version = audio_payload.get("version")
    domain_ref = domain_ref_for_script(db, script)

    payload: Dict[str, Any] = {
        "generation_method": "timeline_pipeline",
        "provider_used": "minimax",
        "model_used": str(tts_model),
        "timing_model": timing_model,
        "use_duration_control": bool(params.get("use_duration_control", False)),
        "prompt": getattr(task, "prompt", None),
        "result_ref": {
            "script_id": getattr(script, "id", None),
            "script_business_id": getattr(script, "business_id", None),
            "episode_id": getattr(script, "episode_id", None),
            "episode_business_id": getattr(script, "episode_business_id", None),
            "audio_timeline_version": audio_version,
            "storyboard_version": getattr(script, "storyboard_version", None),
            **domain_ref,
        },
    }
    pipeline_error = safe_dict(params.get("pipeline_error"))
    if pipeline_error:
        payload["error"] = pipeline_error
    return payload
