"""Best-effort matching for legacy storyboard frames without clip IDs."""

from __future__ import annotations

from typing import Any


def find_legacy_storyboard_frame(
    clip: dict[str, Any],
    storyboard_frames: list[dict[str, Any]],
) -> dict[str, Any] | None:
    best_frame: dict[str, Any] | None = None
    best_score = 0
    for frame in storyboard_frames:
        if not _frame_video_url(frame):
            continue
        score = _legacy_frame_match_score(frame, clip)
        if score > best_score:
            best_frame = frame
            best_score = score
    return best_frame if best_score > 0 else None


def _legacy_frame_match_score(
    frame: dict[str, Any],
    clip: dict[str, Any],
) -> int:
    score = 0
    has_lineage_signal = False

    clip_scene_id = _maybe_int(clip.get("scene_id"))
    frame_scene_id = _maybe_int(frame.get("scene_id"))
    if clip_scene_id is not None and frame_scene_id is not None:
        if clip_scene_id != frame_scene_id:
            return 0
        score += 50

    clip_scene_number = _maybe_int(clip.get("scene_number"))
    frame_scene_number = _maybe_int(frame.get("scene_number"))
    if (
        clip_scene_id is None
        and frame_scene_id is None
        and clip_scene_number is not None
        and frame_scene_number is not None
    ):
        if clip_scene_number != frame_scene_number:
            return 0
        score += 30

    if _same_non_empty_value(clip.get("beat_id"), frame.get("beat_id")):
        score += 80
        has_lineage_signal = True

    time_score = _time_overlap_score(frame, clip)
    if time_score:
        score += time_score
        has_lineage_signal = True

    clip_ordinal = _maybe_int(clip.get("ordinal"))
    frame_number = _maybe_int(frame.get("frame_number"))
    if clip_ordinal is not None and clip_ordinal == frame_number:
        score += 20
        has_lineage_signal = True

    return score if has_lineage_signal else 0


def _time_overlap_score(
    frame: dict[str, Any],
    clip: dict[str, Any],
) -> int:
    clip_start = _maybe_int(clip.get("start_ms"))
    clip_end = _maybe_int(clip.get("end_ms"))
    frame_start = _maybe_int(frame.get("start_ms"))
    frame_end = _maybe_int(frame.get("end_ms"))
    if None in {clip_start, clip_end, frame_start, frame_end}:
        return 0
    if clip_end <= clip_start or frame_end <= frame_start:
        return 0
    overlap = min(clip_end, frame_end) - max(clip_start, frame_start)
    if overlap <= 0:
        return 0
    if clip_start == frame_start and clip_end == frame_end:
        return 100
    if frame_start <= clip_start and frame_end >= clip_end:
        return 90
    clip_duration = max(clip_end - clip_start, 1)
    overlap_ratio = overlap / clip_duration
    if overlap_ratio < 0.5:
        return 0
    return int(50 + min(overlap_ratio, 1.0) * 30)


def _frame_video_url(frame: dict[str, Any]) -> str | None:
    for key in ("video_url", "video_oss_url", "result_video_url"):
        value = frame.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    values = frame.get("video_urls")
    if isinstance(values, list):
        for value in values:
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


def _same_non_empty_value(left: Any, right: Any) -> bool:
    if left is None or right is None:
        return False
    left_text = str(left).strip()
    right_text = str(right).strip()
    return bool(left_text and right_text and left_text == right_text)


def _maybe_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None
