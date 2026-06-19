from __future__ import annotations

from typing import Any


def missing_clip_payload(clip: dict[str, Any], clip_id: str) -> dict[str, Any]:
    return {
        "clip_id": clip_id,
        "scene_id": clip.get("scene_id"),
        "scene_number": clip.get("scene_number"),
        "start_ms": _maybe_int(clip.get("start_ms")),
        "end_ms": _maybe_int(clip.get("end_ms")),
        "reason": "missing_video_url",
    }


def _maybe_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None
