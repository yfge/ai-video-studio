"""Resolve and frame-quantize the final render video contract."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Sequence


@dataclass(frozen=True)
class RenderVideoSpec:
    width: int
    height: int
    fps: int
    total_duration_seconds: float

    @property
    def total_frames(self) -> int:
        return max(round(self.total_duration_seconds * self.fps), 1)


def resolve_render_video_spec(
    preset: dict[str, Any] | None,
    timeline_spec: dict[str, Any] | None,
    clip_durations: Sequence[float],
) -> RenderVideoSpec:
    preset = preset if isinstance(preset, dict) else {}
    timeline_spec = timeline_spec if isinstance(timeline_spec, dict) else {}
    resolution = str(
        preset.get("resolution") or timeline_spec.get("resolution") or "720p"
    )
    width, height = _resolution_dimensions(resolution, timeline_spec)
    fps = _bounded_int(preset.get("fps") or timeline_spec.get("fps"), 24, 1, 60)
    duration_ms = _positive_float(timeline_spec.get("duration_ms"))
    duration = duration_ms / 1000 if duration_ms else sum(clip_durations)
    return RenderVideoSpec(width, height, fps, max(duration, 1 / fps))


def allocate_frame_counts(
    durations: Sequence[float],
    spec: RenderVideoSpec,
) -> list[int]:
    """Quantize adjacent clips without accumulating frame drift."""
    if not durations:
        return []
    total_duration = sum(max(float(value), 0) for value in durations)
    if total_duration <= 0:
        return [1] * len(durations)
    scale = spec.total_duration_seconds / total_duration
    counts: list[int] = []
    previous_end = 0
    cumulative = 0.0
    for duration in durations:
        cumulative += max(float(duration), 0) * scale
        end_frame = min(round(cumulative * spec.fps), spec.total_frames)
        counts.append(max(end_frame - previous_end, 1))
        previous_end += counts[-1]
    counts[-1] += spec.total_frames - sum(counts)
    if counts[-1] <= 0:
        raise ValueError("render frame allocation produced an empty final clip")
    return counts


def _resolution_dimensions(
    resolution: str,
    timeline_spec: dict[str, Any],
) -> tuple[int, int]:
    match = re.fullmatch(r"\s*(\d{2,4})\s*[xX]\s*(\d{2,4})\s*", resolution)
    if match:
        return _bounded_dimension(match.group(1)), _bounded_dimension(match.group(2))
    short_side = _bounded_int(resolution.lower().removesuffix("p"), 720, 64, 2160)
    timeline_resolution = str(timeline_spec.get("resolution") or "")
    timeline_match = re.fullmatch(r"\s*(\d+)\s*[xX]\s*(\d+)\s*", timeline_resolution)
    portrait = not timeline_match or int(timeline_match.group(2)) >= int(
        timeline_match.group(1)
    )
    if portrait:
        return short_side, round(short_side * 16 / 9)
    return round(short_side * 16 / 9), short_side


def _bounded_dimension(value: Any) -> int:
    dimension = _bounded_int(value, 720, 64, 4096)
    return dimension if dimension % 2 == 0 else dimension - 1


def _bounded_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        return max(min(int(value), maximum), minimum)
    except (TypeError, ValueError):
        return default


def _positive_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None
