from __future__ import annotations

from typing import Any

from app.models.script import Episode
from app.models.story_structure import Scene


def scene_has_dialogue_audio(scene: Scene, script_id: int) -> bool:
    meta = scene.extra_metadata
    if not isinstance(meta, dict):
        return False
    payload = meta.get("dialogue_audio")
    if not isinstance(payload, dict):
        return False
    if payload.get("script_id") != script_id:
        return False
    return bool(payload.get("oss_url"))


def scene_number_sort_key(scene: Scene) -> tuple[int, int, str]:
    raw = getattr(scene, "scene_number", None)
    num = _to_int(raw)
    if num is None:
        return (1, 0, str(raw or ""))
    return (0, num, str(raw or ""))


def episode_has_audio_timeline(episode: Episode, script_id: int) -> bool:
    meta = episode.extra_metadata if isinstance(episode.extra_metadata, dict) else {}
    timeline = meta.get("audio_timeline") if isinstance(meta, dict) else None
    if not isinstance(timeline, dict):
        return False
    if timeline.get("script_id") != script_id:
        return False
    ep_audio = timeline.get("episode_audio")
    if not isinstance(ep_audio, dict) or not ep_audio.get("oss_url"):
        return False
    beats = timeline.get("beats")
    return isinstance(beats, list) and len(beats) > 0


def _to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
