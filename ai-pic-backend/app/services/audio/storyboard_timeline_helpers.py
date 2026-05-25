"""Helpers for converting audio timeline beats into storyboard frames."""

from __future__ import annotations

from typing import Any, Callable
from uuid import uuid4


def extract_characters(beat: dict[str, Any]) -> list[str]:
    raw = beat.get("characters_involved")
    if isinstance(raw, list):
        return [str(item).strip() for item in raw if str(item).strip()]
    return []


def parse_ms_range(beat: dict[str, Any]) -> tuple[int | None, int | None]:
    start_ms, end_ms = beat.get("start_ms"), beat.get("end_ms")
    if start_ms is None or end_ms is None:
        return None, None
    try:
        start, end = int(start_ms), int(end_ms)
    except Exception:
        return None, None
    return (start, end) if end >= start else (None, None)


def parse_scene_ids(beat: dict[str, Any]) -> tuple[int | None, int | None]:
    scene_id = beat.get("scene_id")
    scene_id_int = (
        int(scene_id)
        if isinstance(scene_id, (int, str)) and str(scene_id).strip()
        else None
    )
    scene_number = beat.get("scene_number")
    try:
        scene_number_int = int(scene_number) if scene_number is not None else None
    except Exception:
        scene_number_int = None
    return scene_id_int, scene_number_int


def try_merge_pause(
    frames: list[dict[str, Any]],
    start_ms: int,
    end_ms: int,
    duration_ms: int,
    scene_number_int: int | None,
) -> bool:
    """Try to merge a short pause into the previous frame."""
    if not frames:
        return False
    last = frames[-1]
    last_end = last.get("end_ms")
    last_scene_number = last.get("scene_number")
    if not (
        isinstance(last_end, int)
        and last_end == start_ms
        and (
            scene_number_int is None
            or last_scene_number is None
            or int(last_scene_number) == scene_number_int
        )
    ):
        return False
    last["end_ms"] = end_ms
    last_start = last.get("start_ms")
    if isinstance(last_start, int):
        last["duration_seconds"] = round((end_ms - last_start) / 1000.0, 3)
    else:
        last["duration_seconds"] = round(
            float(last.get("duration_seconds") or 0.0) + duration_ms / 1000.0,
            3,
        )
    return True


def make_frame(
    *,
    scene_id_int: int | None,
    scene_number_int: int | None,
    scene_index_map: dict[int, int],
    beat_type: str,
    speaker: str | None,
    text: str | None,
    dialogue_action: str | None,
    characters: list[str],
    description: str,
    duration_ms: int,
    start_ms: int,
    end_ms: int,
    frame_number: int,
    build_prompt: Callable[..., str],
) -> dict[str, Any]:
    return {
        "frame_id": str(uuid4()),
        "frame_number": frame_number,
        "scene_id": scene_id_int,
        "scene_number": scene_number_int,
        "scene_index": (
            scene_index_map.get(scene_id_int) if scene_id_int is not None else None
        ),
        "description": description,
        "beat_type": beat_type,
        "speaker_name": speaker,
        "beat_text": text or None,
        "characters": characters[:5] if characters else [],
        "prompt_description": build_prompt(
            beat_type=str(beat_type),
            speaker_name=speaker,
            text=text,
            dialogue_action=dialogue_action,
        ),
        "duration_seconds": round(duration_ms / 1000.0, 3),
        "generation_source": "audio_timeline",
        "generation_method": "audio_timeline",
        "status": "draft",
        "start_ms": start_ms,
        "end_ms": end_ms,
    }


def storyboard_has_assets(existing: dict | None) -> bool:
    if not isinstance(existing, dict):
        return False
    existing_frames = existing.get("frames")
    if not isinstance(existing_frames, list):
        return False
    asset_keys = (
        "image_url",
        "start_image_url",
        "start_image_urls",
        "end_image_url",
        "end_image_urls",
        "video_url",
        "video_urls",
    )
    for frame in existing_frames:
        if not isinstance(frame, dict):
            continue
        if any(frame.get(key) for key in asset_keys):
            return True
    return False


def check_existing_assets(existing: dict) -> None:
    if storyboard_has_assets(existing):
        raise RuntimeError(
            "storyboard_has_assets_refuse_overwrite: set overwrite_existing=true"
        )
