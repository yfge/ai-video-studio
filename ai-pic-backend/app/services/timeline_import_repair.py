"""Repair detection for legacy Timeline imports."""

from __future__ import annotations

from typing import Any

from app.models.timeline import Timeline
from app.services.audio.dialogue_processing.audio_dialogue_filter import (
    should_treat_dialogue_as_action_for_audio,
)


def existing_timeline_needs_audio_track_repair(
    timeline: Timeline,
    *,
    audio_timeline: dict[str, Any],
    source_version: int | None,
) -> bool:
    """Return True when old imports put action/pause beats on audio tracks."""
    if not _same_audio_timeline_version(
        getattr(timeline, "source_audio_timeline_version", None),
        source_version,
    ):
        return False
    spec = timeline.spec if isinstance(timeline.spec, dict) else {}
    tracks = spec.get("tracks")
    if not isinstance(tracks, list):
        return False

    non_dialogue_beat_ids = _non_dialogue_audio_timeline_beat_ids(audio_timeline)
    for track in tracks:
        if not isinstance(track, dict):
            continue
        track_type = str(track.get("track_type") or track.get("type") or "")
        if track_type not in {"dialogue", "subtitle"}:
            continue
        clips = track.get("clips")
        if not isinstance(clips, list):
            continue
        for clip in clips:
            if not isinstance(clip, dict):
                continue
            beat_type = str(clip.get("beat_type") or "").strip().lower()
            beat_id = _clip_beat_id(clip)
            if beat_type and beat_type != "dialogue":
                return True
            if should_treat_dialogue_as_action_for_audio(clip):
                return True
            if beat_id is not None and beat_id in non_dialogue_beat_ids:
                return True
    return False


def _non_dialogue_audio_timeline_beat_ids(
    audio_timeline: dict[str, Any],
) -> set[str]:
    beats = audio_timeline.get("beats")
    if not isinstance(beats, list):
        return set()
    return {
        str(beat.get("beat_id"))
        for beat in beats
        if isinstance(beat, dict)
        and beat.get("beat_id") is not None
        and (
            beat.get("beat_type") != "dialogue"
            or should_treat_dialogue_as_action_for_audio(beat)
        )
    }


def _clip_beat_id(clip: dict[str, Any]) -> str | None:
    for value in (
        clip.get("beat_id"),
        (
            (clip.get("source_refs") or {}).get("scene_beat_id")
            if isinstance(clip.get("source_refs"), dict)
            else None
        ),
        (
            (clip.get("source") or {}).get("beat_id")
            if isinstance(clip.get("source"), dict)
            else None
        ),
    ):
        if value is not None:
            return str(value)
    return None


def _same_audio_timeline_version(left: Any, right: Any) -> bool:
    try:
        return int(left) == int(right)
    except (TypeError, ValueError):
        return False
