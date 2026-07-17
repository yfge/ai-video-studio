from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.services.timeline_video_segmentation_config import (
    VIDEO_MAX_DURATION_MS,
    VIDEO_MIN_DURATION_MS,
    VIDEO_SEGMENTATION_STRATEGY,
    VIDEO_TAIL_MIN_DURATION_MS,
    VIDEO_TARGET_DURATION_MS,
)

DEFAULT_VIDEO_MIN_PAUSE_DURATION_MS = 1500


def video_track_beats(
    beats: list[dict[str, Any]],
    *,
    min_pause_duration_ms: int = DEFAULT_VIDEO_MIN_PAUSE_DURATION_MS,
) -> list[dict[str, Any]]:
    """Build scene-local video windows without changing audio beat timing."""
    del min_pause_duration_ms  # Kept for import-call compatibility.
    windows: list[dict[str, Any]] = []
    for scene_beats in _scene_runs(beats):
        windows.extend(_scene_video_windows(scene_beats))
    return windows


def _scene_runs(beats: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    runs: list[list[dict[str, Any]]] = []
    for beat in beats:
        if not runs or beat.get("scene_id") != runs[-1][-1].get("scene_id"):
            runs.append([])
        runs[-1].append(beat)
    return runs


def _scene_video_windows(scene_beats: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not scene_beats:
        return []
    scene_start = int(scene_beats[0]["start_ms"])
    scene_end = int(scene_beats[-1]["end_ms"])
    cut_points = {scene_start, scene_end}
    cut_points.update(int(beat["end_ms"]) for beat in scene_beats)
    for beat in scene_beats:
        if int(beat["duration_ms"]) <= VIDEO_MAX_DURATION_MS:
            continue
        cursor = int(beat["start_ms"])
        for duration in _balanced_durations(int(beat["duration_ms"]))[:-1]:
            cursor += duration
            cut_points.add(cursor)

    cuts = _best_partition(sorted(cut_points))
    if cuts is None:
        durations = _balanced_durations(scene_end - scene_start)
        cuts = [scene_start]
        for duration in durations:
            cuts.append(cuts[-1] + duration)

    source_use_counts: dict[tuple[Any, Any, Any], int] = {}
    windows: list[dict[str, Any]] = []
    for start_ms, end_ms in zip(cuts, cuts[1:]):
        overlaps = [
            beat
            for beat in scene_beats
            if int(beat["start_ms"]) < end_ms and int(beat["end_ms"]) > start_ms
        ]
        if not overlaps:
            continue
        anchor = overlaps[0]
        anchor_key = _beat_key(anchor)
        part_index = source_use_counts.get(anchor_key, 0) + 1
        for beat in overlaps:
            key = _beat_key(beat)
            source_use_counts[key] = source_use_counts.get(key, 0) + 1
        windows.append(
            _video_window(anchor, overlaps, start_ms, end_ms, part_index=part_index)
        )
    return windows


def _best_partition(candidates: list[int]) -> list[int] | None:
    if len(candidates) < 2:
        return candidates
    scene_duration = candidates[-1] - candidates[0]
    if scene_duration < VIDEO_MIN_DURATION_MS:
        return [candidates[0], candidates[-1]]

    @lru_cache(maxsize=None)
    def solve(index: int) -> tuple[tuple[int, int, int, tuple[int, ...]], ...] | None:
        if index == len(candidates) - 1:
            return ()
        best = None
        for next_index in range(index + 1, len(candidates)):
            duration = candidates[next_index] - candidates[index]
            is_tail = next_index == len(candidates) - 1
            valid = VIDEO_MIN_DURATION_MS <= duration <= VIDEO_MAX_DURATION_MS
            tail = (
                is_tail
                and VIDEO_TAIL_MIN_DURATION_MS <= duration < VIDEO_MIN_DURATION_MS
            )
            if not (valid or tail):
                continue
            rest = solve(next_index)
            if rest is None:
                continue
            score = (
                1 if tail else 0,
                0 if tail else (duration - VIDEO_TARGET_DURATION_MS) ** 2,
                1,
                (candidates[next_index],),
            )
            option = (score,) + rest
            if best is None or _partition_score(option) < _partition_score(best):
                best = option
        return best

    partition = solve(0)
    if partition is None:
        return None
    return [candidates[0], *[item[3][0] for item in partition]]


def _partition_score(
    partition: tuple[tuple[int, int, int, tuple[int, ...]], ...],
) -> tuple[int, int, int, tuple[int, ...]]:
    return (
        sum(item[0] for item in partition),
        sum(item[1] for item in partition),
        sum(item[2] for item in partition),
        tuple(item[3][0] for item in partition),
    )


def _balanced_durations(total_ms: int) -> list[int]:
    if total_ms <= VIDEO_MAX_DURATION_MS:
        return [total_ms]
    candidates: list[tuple[tuple[int, int, int], list[int]]] = []
    max_parts = max(2, total_ms // VIDEO_TAIL_MIN_DURATION_MS + 1)
    for count in range(2, max_parts + 1):
        normal = _even_durations(total_ms, count)
        if all(
            VIDEO_MIN_DURATION_MS <= value <= VIDEO_MAX_DURATION_MS for value in normal
        ):
            candidates.append((_duration_score(normal, tail=False), normal))
        for tail_ms in range(VIDEO_TAIL_MIN_DURATION_MS, VIDEO_MIN_DURATION_MS):
            leading = _even_durations(total_ms - tail_ms, count - 1)
            if leading and all(
                VIDEO_MIN_DURATION_MS <= value <= VIDEO_MAX_DURATION_MS
                for value in leading
            ):
                values = [*leading, tail_ms]
                candidates.append((_duration_score(values, tail=True), values))
    if not candidates:
        count = max(1, (total_ms + VIDEO_MAX_DURATION_MS - 1) // VIDEO_MAX_DURATION_MS)
        return _even_durations(total_ms, count)
    return min(candidates, key=lambda item: item[0])[1]


def _even_durations(total_ms: int, count: int) -> list[int]:
    if count <= 0:
        return []
    base, remainder = divmod(total_ms, count)
    return [base + (1 if index < remainder else 0) for index in range(count)]


def _duration_score(values: list[int], *, tail: bool) -> tuple[int, int, int]:
    scored_values = values[:-1] if tail else values
    return (
        1 if tail else 0,
        sum((value - VIDEO_TARGET_DURATION_MS) ** 2 for value in scored_values),
        len(values),
    )


def _video_window(
    anchor: dict[str, Any],
    overlaps: list[dict[str, Any]],
    start_ms: int,
    end_ms: int,
    *,
    part_index: int,
) -> dict[str, Any]:
    texts = _unique(beat.get("text") for beat in overlaps)
    speakers = _unique(beat.get("speaker_name") for beat in overlaps)
    characters = _unique_items(
        character
        for beat in overlaps
        for character in (beat.get("characters_involved") or [])
    )
    ranges = [
        {
            "scene_id": beat.get("scene_id"),
            "beat_id": beat.get("beat_id"),
            "ordinal": beat.get("ordinal"),
            "beat_type": beat.get("beat_type"),
            "start_ms": beat.get("start_ms"),
            "end_ms": beat.get("end_ms"),
            "text": beat.get("text"),
            "speaker_name": beat.get("speaker_name"),
            "dialogue_action": beat.get("dialogue_action"),
            "dialogue_emotion": beat.get("dialogue_emotion"),
            "characters_involved": beat.get("characters_involved") or [],
        }
        for beat in overlaps
    ]
    exact_source = (
        len(overlaps) == 1
        and start_ms == int(anchor["start_ms"])
        and end_ms == int(anchor["end_ms"])
    )
    return {
        **anchor,
        "beat_type": anchor.get("beat_type") if exact_source else "beat_window",
        "start_ms": start_ms,
        "end_ms": end_ms,
        "duration_ms": end_ms - start_ms,
        "text": "\n".join(texts),
        "texts": texts,
        "speaker_names": speakers,
        "characters_involved": characters,
        "grouped_beat_ids": [
            beat.get("beat_id") for beat in overlaps if beat.get("beat_id") is not None
        ],
        "source_beat_types": _unique(beat.get("beat_type") for beat in overlaps),
        "source_beat_ranges": ranges,
        "video_part_index": part_index,
        "video_segmentation_strategy": VIDEO_SEGMENTATION_STRATEGY,
    }


def _beat_key(beat: dict[str, Any]) -> tuple[Any, Any, Any]:
    return (beat.get("scene_id"), beat.get("beat_id"), beat.get("ordinal"))


def _unique(values: Any) -> list[str]:
    result: list[str] = []
    for value in values:
        if isinstance(value, str) and value.strip() and value.strip() not in result:
            result.append(value.strip())
    return result


def _unique_items(values: Any) -> list[Any]:
    result: list[Any] = []
    for value in values:
        if value not in result:
            result.append(value)
    return result
