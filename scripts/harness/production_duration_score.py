"""Beat duration checks for provider-chain script scoring."""

from __future__ import annotations

from typing import Any


def duration_failed_checks(
    scenes: list[dict[str, Any]],
    *,
    tolerance_seconds: float = 1.0,
    tolerance_ratio: float = 0.15,
    max_opening_hook_seconds: float = 3.0,
) -> list[str]:
    failed: list[str] = []
    for scene_index, scene in enumerate(scenes, start=1):
        target = _number(scene.get("duration_seconds"))
        beats = scene.get("beats") if isinstance(scene.get("beats"), list) else []
        if target is None or target <= 0 or not beats:
            continue

        durations: list[float] = []
        for beat in beats:
            if not isinstance(beat, dict):
                continue
            duration = _number(beat.get("duration_seconds"))
            if duration is None or duration <= 0:
                failed.append("beat_duration_required")
                continue
            durations.append(duration)

        if "beat_duration_required" in failed or not durations:
            continue

        if scene_index == 1 and durations[0] > max_opening_hook_seconds:
            failed.append("opening_hook_duration")

        total = sum(durations)
        tolerance = max(tolerance_seconds, target * tolerance_ratio)
        if abs(total - target) > tolerance:
            failed.append("scene_duration_alignment")

    return failed


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None
