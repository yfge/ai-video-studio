"""Payload helpers for Timeline clip keyframe tasks."""

from __future__ import annotations

from typing import Any

from app.services.storyboard.grid_storyboard_sheet_payload import string_value


def keyframe_frames(payload: dict[str, Any]) -> list[dict[str, str]]:
    frames = [
        frame
        for frame in payload.get("frames") or []
        if isinstance(frame, dict)
        and string_value(frame.get("role"))
        and string_value(frame.get("prompt"))
    ]
    if not frames:
        raise RuntimeError("timeline_clip_keyframe_frames_missing")
    return [
        {"role": str(frame["role"]), "prompt": str(frame["prompt"])} for frame in frames
    ]


def keyframe_metadata(
    result: dict[str, Any],
    payload: dict[str, Any],
    task_id: int,
    role: str,
) -> dict[str, Any]:
    return {
        "kind": "timeline_clip_keyframe",
        "role": role,
        "task_id": task_id,
        "timeline_id": payload.get("timeline_id"),
        "timeline_version": payload.get("timeline_version"),
        "clip_id": payload.get("clip_id"),
        "provider": result.get("provider"),
        "model": result.get("model") or payload.get("model"),
        "image_gen": result.get("image_gen"),
    }
