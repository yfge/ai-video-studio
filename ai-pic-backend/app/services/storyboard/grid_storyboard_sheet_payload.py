"""Payload helpers for Timeline grid storyboard sheet tasks."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.services.storyboard.grid_storyboard_prompt_bridge import (
    build_grid_storyboard_panels,
)

PANEL_SIGNATURE_KEYS = (
    "panel_index",
    "row",
    "column",
    "clip_id",
    "scene_id",
    "beat_id",
    "start_ms",
    "end_ms",
    "duration_ms",
    "visual_prompt",
    "video_prompt",
    "direction_anchor",
    "aesthetic_reference",
    "shot_type",
    "camera_movement",
    "composition_geometry",
    "motion_timeline",
    "emotional_landing",
    "prompt_method",
    "storyboard_panel_prompt",
)


def grid_payload_matches_current_timeline(timeline, payload: dict[str, Any]) -> bool:
    payload_panels = payload.get("panels")
    if not isinstance(payload_panels, list) or not payload_panels:
        return False
    if payload.get("kind") == "timeline_clip_storyboard":
        return clip_payload_matches_current_timeline(timeline, payload)
    panel_count = maybe_int(payload.get("panel_count")) or len(payload_panels)
    current_panels = build_grid_storyboard_panels(
        timeline.spec if isinstance(timeline.spec, dict) else {},
        panel_count,
    )
    return panel_snapshot_matches_current(payload_panels, current_panels)


def clip_payload_matches_current_timeline(timeline, payload: dict[str, Any]) -> bool:
    clip_id = string_value(payload.get("clip_id"))
    payload_panels = payload.get("panels")
    if not clip_id or not isinstance(payload_panels, list) or not payload_panels:
        return False
    current_clip = _clip_by_id(timeline.spec if isinstance(timeline.spec, dict) else {}, clip_id)
    if current_clip is None:
        return False
    from app.services.storyboard.grid_storyboard_prompt_bridge import (
        build_clip_storyboard_panels,
    )

    panel_count = maybe_int(payload.get("panel_count")) or len(payload_panels)
    current_panels = build_clip_storyboard_panels(current_clip, panel_count)
    return panel_snapshot_matches_current(payload_panels, current_panels)


def panel_snapshot_matches_current(
    payload_panels: list[Any],
    current_panels: list[dict[str, Any]],
) -> bool:
    if len(payload_panels) != len(current_panels):
        return False
    for payload_panel, current_panel in zip(payload_panels, current_panels):
        if not isinstance(payload_panel, dict) or not isinstance(current_panel, dict):
            return False
        for key in PANEL_SIGNATURE_KEYS:
            if key not in payload_panel:
                continue
            if normalized_panel_value(payload_panel.get(key)) != (
                normalized_panel_value(current_panel.get(key))
            ):
                return False
    return True


def sheet_metadata(
    result: dict[str, Any],
    payload: dict[str, Any],
    task_id: int,
) -> dict[str, Any]:
    return {
        "kind": payload.get("kind") or "timeline_storyboard_grid",
        "task_id": task_id,
        "timeline_id": payload.get("timeline_id"),
        "timeline_version": payload.get("timeline_version"),
        "clip_id": payload.get("clip_id"),
        "provider": result.get("provider"),
        "model": result.get("model") or payload.get("model"),
        "image_gen": result.get("image_gen"),
        "panel_count": payload.get("panel_count"),
        "columns": payload.get("columns"),
        "rows": payload.get("rows"),
    }


def _clip_by_id(spec: dict[str, Any], clip_id: str) -> dict[str, Any] | None:
    for track in spec.get("tracks") or []:
        if not isinstance(track, dict):
            continue
        track_type = track.get("track_type") or track.get("type")
        for clip in track.get("clips") or []:
            if isinstance(clip, dict) and (clip.get("clip_id") or clip.get("id")) == clip_id:
                return {**clip, "track_type": clip.get("track_type") or track_type}
    return None


def utc_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")


def maybe_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def string_value(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def normalized_panel_value(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return tuple(normalized_panel_value(item) for item in value)
    if isinstance(value, dict):
        return tuple(
            (str(key), normalized_panel_value(item))
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        )
    return value
