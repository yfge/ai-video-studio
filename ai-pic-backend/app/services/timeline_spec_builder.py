from __future__ import annotations

from typing import Any

from app.models.script import Episode, Script
from app.services.audio.dialogue_processing.audio_dialogue_filter import (
    should_treat_dialogue_as_action_for_audio,
)
from app.services.timeline_video_pause_policy import (
    DEFAULT_VIDEO_MIN_PAUSE_DURATION_MS,
    video_track_beats,
)


def build_timeline_spec_from_audio_timeline(
    *,
    episode: Episode,
    script: Script,
    audio_timeline: dict[str, Any],
    version: int = 1,
    min_pause_duration_ms: int = DEFAULT_VIDEO_MIN_PAUSE_DURATION_MS,
) -> dict[str, Any]:
    beats = audio_timeline.get("beats")
    if not isinstance(beats, list) or not beats:
        raise RuntimeError("audio_timeline_missing_beats")

    source_version = audio_timeline_version(audio_timeline)
    normalized_beats = _normalize_beats(beats)
    dialogue_beats = _filter_dialogue_beats(normalized_beats)
    video_beats = video_track_beats(
        normalized_beats,
        min_pause_duration_ms=min_pause_duration_ms,
    )
    duration_ms = max((beat["end_ms"] for beat in normalized_beats), default=0)
    episode_audio = audio_timeline.get("episode_audio")
    if not isinstance(episode_audio, dict):
        episode_audio = {}

    return {
        "spec_version": "timeline.v1",
        "episode_id": episode.id,
        "episode_business_id": episode.business_id,
        "script_id": script.id,
        "script_business_id": script.business_id,
        "version": version,
        "source_audio_timeline_version": source_version,
        "fps": 24,
        "resolution": "1080x1920",
        "duration_ms": duration_ms,
        "source": {
            "type": "audio_timeline",
            "episode_audio": {
                "oss_url": episode_audio.get("oss_url"),
                "duration_seconds": episode_audio.get("duration_seconds"),
                "generated_at": episode_audio.get("generated_at"),
                "version": source_version,
            },
        },
        "tracks": [
            {
                "track_type": "dialogue",
                "clips": [
                    _clip("dialogue", beat, source_version, episode_audio)
                    for beat in dialogue_beats
                ],
            },
            {
                "track_type": "video",
                "clips": [
                    _clip("video", beat, source_version, episode_audio)
                    for beat in video_beats
                ],
            },
            {
                "track_type": "subtitle",
                "clips": [
                    _clip("subtitle", beat, source_version, episode_audio)
                    for beat in dialogue_beats
                    if beat.get("text")
                ],
            },
        ],
        "support_views": {
            "storyboard": {
                "role": "support_view",
                "legacy_path": "scripts.extra_metadata.storyboard.frames",
                "source": "timeline.v1",
            }
        },
    }


def stable_clip_id(
    *,
    track_type: str,
    scene_id: Any,
    beat_id: Any,
    ordinal: int,
) -> str:
    return (
        f"{_slug(track_type)}_scene_{_slug(scene_id)}_beat_{_slug(beat_id)}_"
        f"{ordinal:03d}"
    )


def audio_timeline_version(audio_timeline: dict[str, Any]) -> int | None:
    episode_audio = audio_timeline.get("episode_audio")
    if not isinstance(episode_audio, dict):
        return None
    value = episode_audio.get("version")
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_beats(beats: list[Any]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for beat in beats:
        if not isinstance(beat, dict):
            continue
        start_ms = _int_ms(beat.get("start_ms"))
        end_ms = _int_ms(beat.get("end_ms"))
        if start_ms is None or end_ms is None:
            raise RuntimeError("audio_timeline_beat_missing_timing")
        if end_ms < start_ms:
            raise RuntimeError("audio_timeline_beat_invalid_timing")
        normalized_beat = {**beat, "start_ms": start_ms, "end_ms": end_ms}
        if should_treat_dialogue_as_action_for_audio(normalized_beat):
            normalized_beat["source_beat_type"] = normalized_beat.get("beat_type")
            normalized_beat["beat_type"] = "action"
            normalized_beat["audio_excluded_reason"] = "fallback_narration"
        normalized.append(normalized_beat)

    normalized.sort(key=lambda item: (item["start_ms"], item["end_ms"]))
    previous_end = 0
    for ordinal, beat in enumerate(normalized, start=1):
        if beat["start_ms"] < previous_end:
            raise RuntimeError("audio_timeline_beats_not_monotonic")
        beat["duration_ms"] = beat["end_ms"] - beat["start_ms"]
        beat["ordinal"] = ordinal
        previous_end = beat["end_ms"]

    if not normalized:
        raise RuntimeError("audio_timeline_missing_beats")
    return normalized


def _filter_dialogue_beats(beats: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [beat for beat in beats if beat.get("beat_type") == "dialogue"]


def _clip(
    track_type: str,
    beat: dict[str, Any],
    source_version: int | None,
    episode_audio: dict[str, Any],
) -> dict[str, Any]:
    scene_id = beat.get("scene_id")
    beat_id = beat.get("beat_id")
    ordinal = int(beat["ordinal"])
    clip = {
        "clip_id": stable_clip_id(
            track_type=track_type,
            scene_id=scene_id,
            beat_id=beat_id,
            ordinal=ordinal,
        ),
        "track_type": track_type,
        "scene_id": scene_id,
        "scene_number": beat.get("scene_number"),
        "beat_id": beat_id,
        "beat_type": beat.get("beat_type"),
        "ordinal": ordinal,
        "start_ms": beat["start_ms"],
        "end_ms": beat["end_ms"],
        "duration_ms": beat["duration_ms"],
        "timing_source": "audio_timeline.beats",
        "source": {
            "kind": "audio_timeline_beat",
            "scene_id": scene_id,
            "beat_id": beat_id,
            "audio_timeline_version": source_version,
        },
        "source_refs": {
            "scene_beat_id": beat_id,
            "audio_timeline_version": source_version,
        },
        "text": beat.get("text"),
    }
    if beat.get("characters_involved"):
        clip["characters_involved"] = beat.get("characters_involved")
    if beat.get("speaker_name"):
        clip["speaker_name"] = beat.get("speaker_name")
    if beat.get("dialogue_action"):
        clip["dialogue_action"] = beat.get("dialogue_action")
    if beat.get("dialogue_emotion"):
        clip["dialogue_emotion"] = beat.get("dialogue_emotion")
    if beat.get("audio_excluded_reason"):
        clip["audio_excluded_reason"] = beat.get("audio_excluded_reason")
    if beat.get("source_beat_type"):
        clip["source_beat_type"] = beat.get("source_beat_type")
    if beat.get("absorbed_pause_beat_ids"):
        clip["absorbed_pause_beat_ids"] = beat.get("absorbed_pause_beat_ids")
        clip["absorbed_pause_ranges"] = beat.get("absorbed_pause_ranges") or []
        clip["absorbed_pause_duration_ms"] = beat.get("absorbed_pause_duration_ms") or 0
        clip["source_refs"]["absorbed_pause_beat_ids"] = beat.get(
            "absorbed_pause_beat_ids"
        )
    if track_type == "dialogue":
        clip["asset_ref"] = {
            "kind": "episode_audio",
            "url": episode_audio.get("oss_url"),
            "start_ms": beat["start_ms"],
            "duration_ms": beat["duration_ms"],
        }
    elif track_type == "video":
        clip["asset_ref"] = None
        clip["placeholder"] = True
    elif track_type == "subtitle":
        clip["asset_ref"] = None
    return clip


def _int_ms(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _slug(value: Any) -> str:
    raw = str(value if value is not None else "unknown").strip().lower()
    safe = [ch if ch.isalnum() else "_" for ch in raw]
    slug = "".join(safe).strip("_")
    return slug or "unknown"
