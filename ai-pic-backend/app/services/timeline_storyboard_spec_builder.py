from __future__ import annotations

from typing import Any

from app.models.script import Episode, Script
from app.services.timeline_spec_builder import stable_clip_id


def build_timeline_spec_from_storyboard_frames(
    *,
    episode: Episode,
    script: Script,
    storyboard_frames: list[dict[str, Any]],
    version: int = 1,
    source_audio_timeline_version: int | None = None,
) -> dict[str, Any]:
    """Build a Timeline Spec v1 video track from legacy storyboard video assets."""
    normalized_frames = _normalize_storyboard_frames(storyboard_frames)
    if not normalized_frames:
        raise RuntimeError("storyboard_video_frames_not_found")
    duration_ms = max((frame["end_ms"] for frame in normalized_frames), default=0)

    return {
        "spec_version": "timeline.v1",
        "episode_id": episode.id,
        "episode_business_id": episode.business_id,
        "script_id": script.id,
        "script_business_id": script.business_id,
        "version": version,
        "source_audio_timeline_version": source_audio_timeline_version,
        "fps": 24,
        "resolution": "1080x1920",
        "duration_ms": duration_ms,
        "source": {
            "type": "legacy_storyboard",
            "legacy_path": "scripts.extra_metadata.storyboard.frames",
            "source_audio_timeline_version": source_audio_timeline_version,
        },
        "tracks": [
            {
                "track_type": "video",
                "clips": [
                    _storyboard_video_clip(frame, ordinal)
                    for ordinal, frame in enumerate(normalized_frames, start=1)
                ],
            }
        ],
        "support_views": {
            "storyboard": {
                "role": "support_view",
                "legacy_path": "scripts.extra_metadata.storyboard.frames",
                "source": "legacy_storyboard",
            }
        },
    }


def _normalize_storyboard_frames(frames: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    cursor_ms = 0
    for index, frame in enumerate(frames, start=1):
        if not isinstance(frame, dict):
            continue
        video_url = _storyboard_video_url(frame)
        if not video_url:
            continue
        start_ms = _int_ms(frame.get("start_ms"))
        end_ms = _int_ms(frame.get("end_ms"))
        if start_ms is None or end_ms is None or end_ms <= start_ms:
            duration_ms = _storyboard_duration_ms(frame)
            start_ms = cursor_ms
            end_ms = start_ms + duration_ms
        cursor_ms = max(cursor_ms, end_ms)
        normalized.append(
            {
                **frame,
                "frame_index": index - 1,
                "start_ms": start_ms,
                "end_ms": end_ms,
                "duration_ms": end_ms - start_ms,
                "video_url": video_url,
            }
        )
    normalized.sort(key=lambda item: (item["start_ms"], item["end_ms"]))
    return normalized


def _storyboard_video_clip(frame: dict[str, Any], ordinal: int) -> dict[str, Any]:
    frame_id = frame.get("frame_id") or frame.get("id") or ordinal
    scene_id = frame.get("scene_id") or frame.get("scene_number")
    beat_id = f"storyboard_{frame_id}"
    return {
        "clip_id": stable_clip_id(
            track_type="video",
            scene_id=scene_id,
            beat_id=beat_id,
            ordinal=ordinal,
        ),
        "track_type": "video",
        "scene_id": scene_id,
        "scene_number": frame.get("scene_number"),
        "beat_id": beat_id,
        "frame_number": frame.get("frame_number") or ordinal,
        "storyboard_frame_id": frame_id,
        "ordinal": ordinal,
        "start_ms": frame["start_ms"],
        "end_ms": frame["end_ms"],
        "duration_ms": frame["duration_ms"],
        "timing_source": "legacy_storyboard.frames",
        "source": {
            "kind": "legacy_storyboard_frame",
            "storyboard_frame_id": frame_id,
            "frame_number": frame.get("frame_number") or ordinal,
            "scene_id": scene_id,
            "beat_id": beat_id,
        },
        "source_refs": {
            "storyboard_frame_id": frame_id,
            "frame_index": frame.get("frame_index"),
        },
        "asset_ref": {
            "kind": "legacy_storyboard_video",
            "url": frame["video_url"],
            "storyboard_frame_id": frame_id,
            "frame_number": frame.get("frame_number") or ordinal,
        },
        "video_url": frame["video_url"],
        "placeholder": False,
        "text": frame.get("description") or frame.get("beat_text"),
    }


def _storyboard_video_url(frame: dict[str, Any]) -> str | None:
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


def _storyboard_duration_ms(frame: dict[str, Any]) -> int:
    duration_ms = _int_ms(frame.get("duration_ms"))
    if duration_ms and duration_ms > 0:
        return duration_ms
    duration_seconds = frame.get("duration_seconds")
    try:
        seconds = float(duration_seconds)
    except (TypeError, ValueError):
        seconds = 3.0
    return max(int(round(seconds * 1000)), 100)


def _int_ms(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
