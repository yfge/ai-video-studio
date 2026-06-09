"""Timeline Spec mutation helpers for clip keyframes."""

from __future__ import annotations

import copy
from typing import Any

from app.models.timeline import MediaAsset


def apply_clip_keyframes_to_spec(
    spec: dict[str, Any],
    *,
    clip_id: str,
    frames: dict[str, MediaAsset],
    prompt_sha256_by_role: dict[str, str],
    source_timeline_version: int,
    generated_at: str,
) -> dict[str, Any]:
    updated = copy.deepcopy(spec)
    frame_refs = {
        role: _asset_ref(
            role,
            asset,
            prompt_sha256=prompt_sha256_by_role.get(role),
            source_timeline_version=source_timeline_version,
            generated_at=generated_at,
        )
        for role, asset in frames.items()
    }
    support_views = updated.setdefault("support_views", {})
    clip_keyframes = support_views.setdefault("clip_keyframes", {})
    clip_keyframes[clip_id] = {
        "mode": "clip_keyframes.v1",
        "frames": frame_refs,
        "generated_at": generated_at,
        "source": "timeline_spec_clip",
        "source_timeline_version": source_timeline_version,
    }
    _attach_keyframe_refs_to_clip(updated, clip_id, frame_refs)
    return updated


def _attach_keyframe_refs_to_clip(
    spec: dict[str, Any],
    clip_id: str,
    frame_refs: dict[str, dict[str, Any]],
) -> None:
    for track in spec.get("tracks") or []:
        if not isinstance(track, dict):
            continue
        track_type = track.get("track_type") or track.get("type")
        if track_type != "video":
            continue
        for clip in track.get("clips") or []:
            if not isinstance(clip, dict):
                continue
            if (clip.get("clip_id") or clip.get("id")) != clip_id:
                continue
            refs = clip.setdefault("source_refs", {})
            refs["clip_keyframes"] = {
                "mode": "clip_keyframes.v1",
                "start_frame_media_asset_id": _asset_id(frame_refs.get("start_frame")),
                "end_frame_media_asset_id": _asset_id(frame_refs.get("end_frame")),
            }
            if "start_frame" in frame_refs:
                clip["start_frame_asset_ref"] = frame_refs["start_frame"]
            if "end_frame" in frame_refs:
                clip["end_frame_asset_ref"] = frame_refs["end_frame"]


def _asset_ref(
    role: str,
    asset: MediaAsset,
    *,
    prompt_sha256: str | None,
    source_timeline_version: int,
    generated_at: str,
) -> dict[str, Any]:
    file_url = asset.file_url or asset.file_path
    return {
        "kind": role,
        "role": role,
        "media_asset_id": asset.id,
        "file_url": file_url,
        "file_path": asset.file_path,
        "prompt_sha256": prompt_sha256,
        "source_timeline_version": source_timeline_version,
        "generated_at": generated_at,
    }


def _asset_id(asset_ref: dict[str, Any] | None) -> int | None:
    value = asset_ref.get("media_asset_id") if isinstance(asset_ref, dict) else None
    return int(value) if isinstance(value, int) else None
