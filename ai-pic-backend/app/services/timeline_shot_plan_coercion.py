from __future__ import annotations

from copy import deepcopy
from typing import Any


def coerce_timeline_shot_plan_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}

    normalized = deepcopy(payload)
    shots = normalized.get("shots")
    if not isinstance(shots, list):
        return normalized

    for shot in shots:
        if not isinstance(shot, dict):
            continue
        duration_ms = _coerce_int(shot.get("duration_ms"))
        motion_timeline = shot.get("motion_timeline")
        if not isinstance(motion_timeline, list):
            continue

        motion_points: list[dict[str, Any]] = []
        fallback_action = (
            _strip_text(shot.get("action"))
            or _strip_text(shot.get("plot"))
            or "hold the visual beat"
        )
        for point in motion_timeline:
            if not isinstance(point, dict):
                continue
            at_ms = _coerce_int(point.get("at_ms"))
            if at_ms is None:
                continue
            action = _strip_text(point.get("action")) or fallback_action
            motion_points.append({"at_ms": at_ms, "action": action})

        if motion_points:
            motion_points = sorted(motion_points, key=lambda item: item["at_ms"])
            limited = _limit_motion_timeline(motion_points)
            if duration_ms is not None and len(motion_points) > 4:
                limited = [
                    {
                        **point,
                        "at_ms": max(0, min(point["at_ms"], duration_ms)),
                    }
                    for point in limited
                ]
            shot["motion_timeline"] = limited

    return normalized


def _coerce_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            return int(float(stripped))
        except ValueError:
            return None
    return None


def _limit_motion_timeline(points: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if len(points) <= 4:
        return points
    last_index = len(points) - 1
    indexes = {
        0,
        round(last_index / 3),
        round((last_index * 2) / 3),
        last_index,
    }
    return [points[index] for index in sorted(indexes)]


def _strip_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""
