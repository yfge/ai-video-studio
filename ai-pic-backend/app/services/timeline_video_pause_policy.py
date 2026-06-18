from __future__ import annotations

from typing import Any

DEFAULT_VIDEO_MIN_PAUSE_DURATION_MS = 1500


def video_track_beats(
    beats: list[dict[str, Any]],
    *,
    min_pause_duration_ms: int = DEFAULT_VIDEO_MIN_PAUSE_DURATION_MS,
) -> list[dict[str, Any]]:
    video_beats: list[dict[str, Any]] = []
    pause_threshold = max(0, int(min_pause_duration_ms or 0))

    for beat in beats:
        video_beat = dict(beat)
        if (
            video_beat.get("beat_type") == "pause"
            and int(video_beat.get("duration_ms") or 0) < pause_threshold
            and _absorb_short_pause(video_beats, video_beat)
        ):
            continue
        video_beats.append(video_beat)

    return video_beats


def _absorb_short_pause(
    video_beats: list[dict[str, Any]],
    pause: dict[str, Any],
) -> bool:
    if not video_beats:
        return False
    previous = video_beats[-1]
    previous_end = previous.get("end_ms")
    pause_start = pause.get("start_ms")
    pause_end = pause.get("end_ms")
    if not (
        isinstance(previous_end, int)
        and isinstance(pause_start, int)
        and isinstance(pause_end, int)
        and previous_end == pause_start
    ):
        return False

    previous["end_ms"] = pause_end
    previous_start = previous.get("start_ms")
    if isinstance(previous_start, int):
        previous["duration_ms"] = pause_end - previous_start
    else:
        previous["duration_ms"] = int(previous.get("duration_ms") or 0) + int(
            pause.get("duration_ms") or 0
        )
    previous.setdefault("absorbed_pause_beat_ids", []).append(pause.get("beat_id"))
    previous.setdefault("absorbed_pause_ranges", []).append(
        {
            "beat_id": pause.get("beat_id"),
            "start_ms": pause_start,
            "end_ms": pause_end,
            "duration_ms": pause.get("duration_ms"),
        }
    )
    previous["absorbed_pause_duration_ms"] = int(
        previous.get("absorbed_pause_duration_ms") or 0
    ) + int(pause.get("duration_ms") or 0)
    return True
