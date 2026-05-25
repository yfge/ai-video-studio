"""Timeline Spec v1 structural validation."""

from __future__ import annotations

from typing import Any

from app.services.timeline_spec_source_validation import validate_clip_source_and_assets
from app.services.timeline_spec_validation_types import fail as _fail
from app.services.timeline_spec_validation_types import (
    match_optional_id as _match_optional_id,
)
from app.services.timeline_spec_validation_types import (
    non_empty_string as _non_empty_string,
)
from app.services.timeline_spec_validation_types import required_int as _required_int
from app.services.timeline_spec_validation_types import (
    required_present as _required_present,
)
from app.services.timeline_spec_validation_types import (
    required_string as _required_string,
)

ALLOWED_TRACK_TYPES = {"dialogue", "video", "subtitle", "bgm", "sfx"}


def validate_timeline_spec(
    spec: dict[str, Any],
    *,
    episode_id: int | None = None,
    script_id: int | None = None,
    timeline_id: int | None = None,
    expected_version: int | None = None,
    require_timeline_id: bool = False,
) -> None:
    if not isinstance(spec, dict):
        _fail("timeline_spec_not_object", "spec", "Timeline spec must be an object")

    _validate_envelope(
        spec,
        episode_id=episode_id,
        script_id=script_id,
        timeline_id=timeline_id,
        expected_version=expected_version,
        require_timeline_id=require_timeline_id,
    )
    tracks = spec.get("tracks")
    if not isinstance(tracks, list) or not tracks:
        _fail(
            "timeline_spec_missing_tracks", "tracks", "tracks must be a non-empty list"
        )

    seen_clip_ids: set[str] = set()
    max_end_ms = 0
    total_clips = 0
    for track_index, track in enumerate(tracks):
        path = f"tracks[{track_index}]"
        track_type, clips = _validate_track(track, path)
        previous_end = 0
        for clip_index, clip in enumerate(clips):
            total_clips += 1
            clip_path = f"{path}.clips[{clip_index}]"
            end_ms = _validate_clip(
                clip,
                clip_path,
                track_type=track_type,
                previous_end_ms=previous_end,
                seen_clip_ids=seen_clip_ids,
            )
            previous_end = end_ms
            max_end_ms = max(max_end_ms, end_ms)

    if total_clips == 0:
        _fail("timeline_spec_missing_clips", "tracks", "at least one clip is required")
    duration_ms = _required_int(spec, "duration_ms", "duration_ms", min_value=0)
    if duration_ms < max_end_ms:
        _fail(
            "timeline_spec_duration_too_short",
            "duration_ms",
            "duration_ms must cover the latest clip end_ms",
        )


def _validate_envelope(
    spec: dict[str, Any],
    *,
    episode_id: int | None,
    script_id: int | None,
    timeline_id: int | None,
    expected_version: int | None,
    require_timeline_id: bool,
) -> None:
    if spec.get("spec_version") != "timeline.v1":
        _fail(
            "timeline_spec_version_invalid",
            "spec_version",
            "spec_version must be timeline.v1",
        )
    _match_optional_id(spec, "episode_id", episode_id)
    _match_optional_id(spec, "script_id", script_id)
    if require_timeline_id or spec.get("timeline_id") is not None:
        _match_optional_id(spec, "timeline_id", timeline_id)
    if expected_version is not None:
        version = _required_int(spec, "version", "version", min_value=1)
        if version != expected_version:
            _fail(
                "timeline_spec_version_mismatch",
                "version",
                f"version must match expected timeline version {expected_version}",
            )
    _required_int(
        spec,
        "source_audio_timeline_version",
        "source_audio_timeline_version",
        min_value=1,
    )
    _required_int(spec, "fps", "fps", min_value=1)
    if not _non_empty_string(spec.get("resolution")):
        _fail(
            "timeline_spec_resolution_invalid", "resolution", "resolution is required"
        )


def _validate_track(track: Any, path: str) -> tuple[str, list[Any]]:
    if not isinstance(track, dict):
        _fail("timeline_spec_track_invalid", path, "track must be an object")
    track_type = track.get("track_type") or track.get("type")
    if not _non_empty_string(track_type) or str(track_type) not in ALLOWED_TRACK_TYPES:
        _fail(
            "timeline_spec_track_type_invalid",
            f"{path}.track_type",
            "track_type must be a supported Timeline Spec v1 track type",
        )
    clips = track.get("clips")
    if not isinstance(clips, list):
        _fail(
            "timeline_spec_track_clips_invalid", f"{path}.clips", "clips must be a list"
        )
    return str(track_type), clips


def _validate_clip(
    clip: Any,
    path: str,
    *,
    track_type: str,
    previous_end_ms: int,
    seen_clip_ids: set[str],
) -> int:
    if not isinstance(clip, dict):
        _fail("timeline_spec_clip_invalid", path, "clip must be an object")
    clip_id = _required_string(clip, "clip_id", f"{path}.clip_id")
    if clip_id in seen_clip_ids:
        _fail(
            "timeline_spec_clip_id_duplicate",
            f"{path}.clip_id",
            "clip_id must be unique",
        )
    seen_clip_ids.add(clip_id)
    clip_track_type = _required_string(clip, "track_type", f"{path}.track_type")
    if clip_track_type != track_type:
        _fail(
            "timeline_spec_clip_track_mismatch",
            f"{path}.track_type",
            "track_type must match parent track",
        )
    _required_int(clip, "ordinal", f"{path}.ordinal", min_value=1)
    _required_present(clip, "scene_id", f"{path}.scene_id")
    _required_present(clip, "beat_id", f"{path}.beat_id")

    start_ms = _required_int(clip, "start_ms", f"{path}.start_ms", min_value=0)
    end_ms = _required_int(clip, "end_ms", f"{path}.end_ms", min_value=0)
    duration_ms = _required_int(clip, "duration_ms", f"{path}.duration_ms", min_value=0)
    if end_ms < start_ms:
        _fail(
            "timeline_spec_clip_timing_invalid",
            f"{path}.end_ms",
            "end_ms must be >= start_ms",
        )
    if duration_ms != end_ms - start_ms:
        _fail(
            "timeline_spec_clip_duration_mismatch",
            f"{path}.duration_ms",
            "duration_ms must equal end_ms - start_ms",
        )
    if start_ms < previous_end_ms:
        _fail(
            "timeline_spec_clip_timing_non_monotonic",
            f"{path}.start_ms",
            "clips must be ordered and non-overlapping per track",
        )

    validate_clip_source_and_assets(clip, path)
    return end_ms
