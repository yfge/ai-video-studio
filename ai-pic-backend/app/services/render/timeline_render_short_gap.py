from __future__ import annotations

from typing import Any

SHORT_GAP_FALLBACK_MAX_SECONDS = 2.0
PreliminaryClip = tuple[dict[str, Any], str, str | None, str]


def resolve_short_gap_neighbor(
    preliminary: list[PreliminaryClip],
    index: int,
    *,
    duration_seconds: float,
) -> tuple[str, str] | None:
    if duration_seconds > SHORT_GAP_FALLBACK_MAX_SECONDS:
        return None
    neighbor = _nearest_ready_neighbor(preliminary, index)
    if neighbor is None:
        return None
    neighbor_clip_id, neighbor_url = neighbor
    return neighbor_url, f"short_gap_neighbor:{neighbor_clip_id}"


def _nearest_ready_neighbor(
    preliminary: list[PreliminaryClip],
    index: int,
) -> tuple[str, str] | None:
    for distance in range(1, len(preliminary)):
        for candidate_index in (index - distance, index + distance):
            if candidate_index < 0 or candidate_index >= len(preliminary):
                continue
            _clip, clip_id, url, _source = preliminary[candidate_index]
            if url:
                return clip_id, url
    return None
