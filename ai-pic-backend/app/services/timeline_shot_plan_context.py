"""Time-overlap context helpers for Timeline shot plans."""

from __future__ import annotations

from typing import Any


def clips_for_track(spec: dict[str, Any], track_type: str) -> list[dict[str, Any]]:
    tracks = spec.get("tracks")
    if not isinstance(tracks, list):
        return []
    for track in tracks:
        if not isinstance(track, dict):
            continue
        if track.get("track_type") == track_type or track.get("type") == track_type:
            clips = track.get("clips")
            return [clip for clip in clips or [] if isinstance(clip, dict)]
    return []


def overlapping_clips(
    spec: dict[str, Any],
    video_clip: dict[str, Any],
    track_type: str,
) -> list[dict[str, Any]]:
    start_ms = int(video_clip.get("start_ms") or 0)
    end_ms = int(video_clip.get("end_ms") or start_ms)
    scene_id = video_clip.get("scene_id")
    return [
        clip
        for clip in clips_for_track(spec, track_type)
        if clip.get("scene_id") == scene_id
        and int(clip.get("start_ms") or 0) < end_ms
        and int(clip.get("end_ms") or 0) > start_ms
    ]


def timed_text(item: dict[str, Any], video_clip: dict[str, Any]) -> dict[str, Any]:
    window_start = int(video_clip.get("start_ms") or 0)
    return {
        "at_ms": max(0, int(item.get("start_ms") or 0) - window_start),
        "end_ms": max(0, int(item.get("end_ms") or 0) - window_start),
        "text": item.get("text") or "",
        "speaker_name": item.get("speaker_name"),
        "dialogue_action": item.get("dialogue_action"),
        "dialogue_emotion": item.get("dialogue_emotion"),
    }


def unique_texts(values: Any) -> list[str]:
    result: list[str] = []
    for value in values:
        text = strip_text(value)
        if text and text not in result:
            result.append(text)
    return result


def strip_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""
