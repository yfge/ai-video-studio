"""Environment context binding for clip storyboard tasks."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from .storyboard_audio_scene_env_hints import load_scene_environment_hints


def build_clip_storyboard_environment_context(
    db: Session,
    *,
    clip: dict[str, Any],
    script_id: int | None,
) -> dict[str, str] | None:
    if not script_id:
        return None
    scene_ids, scene_numbers = _scene_keys(clip)
    env_by_id, env_by_number = load_scene_environment_hints(
        db,
        script_id=script_id,
        scene_ids=scene_ids,
        scene_numbers=scene_numbers,
    )
    env_url, env_hint = _first_context(scene_ids, env_by_id)
    if not (env_url or env_hint):
        env_url, env_hint = _first_context(scene_numbers, env_by_number)
    if not (env_url or env_hint):
        return None
    result: dict[str, str] = {}
    if env_url:
        result["reference_url"] = env_url
    if env_hint:
        result["hint"] = env_hint
    return result


def _scene_keys(clip: dict[str, Any]) -> tuple[list[int], list[int]]:
    scene_ids: list[int] = []
    scene_numbers: list[int] = []
    raw_scene_id = clip.get("scene_id")
    if isinstance(raw_scene_id, int):
        scene_ids.append(raw_scene_id)
        scene_numbers.append(raw_scene_id)
    else:
        parsed = _digits_int(raw_scene_id)
        if parsed:
            scene_numbers.append(parsed)
    scene_number = _maybe_int(clip.get("scene_number"))
    if scene_number:
        scene_numbers.append(scene_number)
    return scene_ids, scene_numbers


def _first_context(
    keys: list[int],
    mapping: dict[int, tuple[str | None, str | None]],
) -> tuple[str | None, str | None]:
    for key in keys:
        env_url, env_hint = mapping.get(key) or (None, None)
        if env_url or env_hint:
            return env_url, env_hint
    return None, None


def _digits_int(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if not isinstance(value, str):
        return None
    digits = "".join(ch for ch in value if ch.isdigit())
    return _maybe_int(digits)


def _maybe_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None and str(value).strip() else None
    except (TypeError, ValueError):
        return None
