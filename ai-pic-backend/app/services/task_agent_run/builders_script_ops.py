from __future__ import annotations

from typing import Any, Dict

from app.services.task_agent_run.utils import (
    loads_task_parameters,
    maybe_int,
    parse_result_id,
    safe_dict,
    split_provider_model,
)


def _load_script_owned(db, *, script_id: int, user_id: int):
    from app.models.script import Episode, Script, Story

    return (
        db.query(Script)
        .join(Episode, Script.episode_id == Episode.id)
        .join(Story, Episode.story_id == Story.id)
        .filter(Script.id == script_id, Story.user_id == user_id)
        .first()
    )


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
        },
    }
    return payload


def build_storyboard_image_agent_run(db, task, *, user_id: int) -> Dict[str, Any]:
    params = loads_task_parameters(getattr(task, "parameters", None))
    script_id = _resolve_script_id(task)
    if script_id is None:
        return {}

    script = _load_script_owned(db, script_id=script_id, user_id=user_id)
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
        },
    }
    keyframe_mode = params.get("keyframe_mode")
    if isinstance(keyframe_mode, str) and keyframe_mode.strip():
        payload["keyframe_mode"] = keyframe_mode
    generation_profile = params.get("generation_profile")
    if isinstance(generation_profile, str) and generation_profile.strip():
        payload["generation_profile"] = generation_profile
    return payload
