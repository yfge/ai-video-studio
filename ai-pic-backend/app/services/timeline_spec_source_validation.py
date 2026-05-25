"""Timeline Spec clip source and asset reference validation."""

from __future__ import annotations

from typing import Any

from app.services.timeline_spec_validation_types import (
    fail,
    match_required_source_value,
    match_value,
    non_empty_string,
    required_int,
    required_present,
)

ALLOWED_SOURCE_KINDS = {
    "scene_beat",
    "audio_timeline_beat",
    "storyboard_frame",
    "legacy_storyboard_frame",
    "manual",
}


def validate_clip_source_and_assets(clip: dict[str, Any], path: str) -> None:
    source = clip.get("source")
    if not isinstance(source, dict):
        fail(
            "timeline_spec_clip_source_invalid",
            f"{path}.source",
            "source must be an object",
        )
    kind = source.get("kind")
    if not non_empty_string(kind) or str(kind) not in ALLOWED_SOURCE_KINDS:
        fail(
            "timeline_spec_clip_source_kind_invalid",
            f"{path}.source.kind",
            "source.kind is invalid",
        )

    source_refs = clip.get("source_refs")
    if source_refs is not None and not isinstance(source_refs, dict):
        fail(
            "timeline_spec_clip_source_refs_invalid",
            f"{path}.source_refs",
            "source_refs must be an object",
        )

    if kind in {"audio_timeline_beat", "scene_beat"}:
        _validate_beat_source(clip, source, source_refs, path, str(kind))
    elif kind in {"storyboard_frame", "legacy_storyboard_frame"}:
        _validate_storyboard_source(clip, source, source_refs, path)
    _validate_asset_ref(clip.get("asset_ref"), f"{path}.asset_ref")


def _validate_beat_source(
    clip: dict[str, Any],
    source: dict[str, Any],
    source_refs: Any,
    path: str,
    kind: str,
) -> None:
    match_required_source_value(clip, source, "scene_id", f"{path}.source.scene_id")
    match_required_source_value(clip, source, "beat_id", f"{path}.source.beat_id")
    if kind == "audio_timeline_beat":
        required_int(
            source,
            "audio_timeline_version",
            f"{path}.source.audio_timeline_version",
            min_value=1,
        )
    if isinstance(source_refs, dict) and source_refs.get("scene_beat_id") is not None:
        match_value(
            source_refs.get("scene_beat_id"),
            clip.get("beat_id"),
            f"{path}.source_refs.scene_beat_id",
            "source_refs.scene_beat_id must match clip beat_id",
        )


def _validate_storyboard_source(
    clip: dict[str, Any],
    source: dict[str, Any],
    source_refs: Any,
    path: str,
) -> None:
    match_required_source_value(clip, source, "scene_id", f"{path}.source.scene_id")
    if source.get("beat_id") is not None:
        match_value(
            source.get("beat_id"),
            clip.get("beat_id"),
            f"{path}.source.beat_id",
            "source.beat_id must match clip beat_id",
        )
    required_present(
        source, "storyboard_frame_id", f"{path}.source.storyboard_frame_id"
    )
    if (
        isinstance(source_refs, dict)
        and source_refs.get("storyboard_frame_id") is not None
    ):
        match_value(
            source_refs.get("storyboard_frame_id"),
            source.get("storyboard_frame_id"),
            f"{path}.source_refs.storyboard_frame_id",
            "source_refs.storyboard_frame_id must match source.storyboard_frame_id",
        )


def _validate_asset_ref(asset_ref: Any, path: str) -> None:
    if asset_ref is None:
        return
    if not isinstance(asset_ref, dict):
        fail("timeline_spec_asset_ref_invalid", path, "asset_ref must be an object")
    for key in ("media_asset_id", "asset_id", "video_asset_id", "audio_asset_id"):
        if key in asset_ref and asset_ref[key] is not None:
            required_int(asset_ref, key, f"{path}.{key}", min_value=1)
    for key in ("url", "file_url", "video_url", "video_oss_url", "file_path"):
        value = asset_ref.get(key)
        if key in asset_ref and value is not None and not non_empty_string(value):
            fail(
                "timeline_spec_asset_ref_url_invalid",
                f"{path}.{key}",
                "asset_ref URL fields must be non-empty strings",
            )
