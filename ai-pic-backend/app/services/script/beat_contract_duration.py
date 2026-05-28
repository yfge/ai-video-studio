from __future__ import annotations

from typing import Any


def duration_issues(
    scene: Any,
    *,
    tolerance_seconds: float = 1.0,
    tolerance_ratio: float = 0.15,
    max_opening_hook_seconds: float = 3.0,
) -> list[dict[str, Any]]:
    target = scene.estimated_duration_seconds
    if target is None or target <= 0:
        return []

    issues: list[dict[str, Any]] = []
    durations: list[float] = []
    for beat in scene.beats:
        duration = beat.duration_seconds
        if duration is None or duration <= 0:
            issues.append(
                {
                    "check_id": "beat_duration_required",
                    "message": "timed scene beats must have positive durations",
                    "scene_number": scene.scene_number,
                    "beat_order_index": beat.order_index,
                    "evidence": {"duration_seconds": duration},
                }
            )
            continue
        durations.append(float(duration))

    if issues:
        return issues

    opening_hook_duration = durations[0] if scene.scene_number == 1 else None
    if (
        opening_hook_duration is not None
        and opening_hook_duration > max_opening_hook_seconds
    ):
        issues.append(
            {
                "check_id": "opening_hook_duration",
                "message": "first hook beat must land within three seconds",
                "scene_number": scene.scene_number,
                "beat_order_index": scene.beats[0].order_index,
                "evidence": {
                    "duration_seconds": opening_hook_duration,
                    "maximum_seconds": max_opening_hook_seconds,
                },
            }
        )

    total = round(sum(durations), 2)
    tolerance = max(tolerance_seconds, float(target) * tolerance_ratio)
    if abs(total - float(target)) > tolerance:
        issues.append(
            {
                "check_id": "scene_duration_alignment",
                "message": "beat durations must align with scene duration",
                "scene_number": scene.scene_number,
                "beat_order_index": None,
                "evidence": {
                    "beat_duration_total": total,
                    "estimated_duration_seconds": target,
                    "tolerance_seconds": round(tolerance, 2),
                },
            }
        )

    return issues
