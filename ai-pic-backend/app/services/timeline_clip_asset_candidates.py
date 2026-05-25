"""Extract first-class clip asset candidates from Timeline Spec clips."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ClipAssetCandidate:
    clip_id: str
    track_type: str | None
    asset_role: str
    asset_type: str
    origin: str
    media_asset_id: int | None = None
    file_url: str | None = None
    file_path: str | None = None
    object_key: str | None = None
    mime_type: str | None = None
    duration_ms: int | None = None
    source: str | None = None
    source_ref: dict[str, Any] | None = None


def timeline_clip_asset_candidates(spec: dict[str, Any]) -> list[ClipAssetCandidate]:
    candidates: list[ClipAssetCandidate] = []
    for clip in _timeline_clips(spec):
        candidates.extend(_clip_asset_candidates(clip))
    return candidates


def _timeline_clips(spec: dict[str, Any]) -> list[dict[str, Any]]:
    clips: list[dict[str, Any]] = []
    tracks = spec.get("tracks")
    if not isinstance(tracks, list):
        return clips
    for track in tracks:
        if not isinstance(track, dict):
            continue
        track_type = track.get("track_type") or track.get("type")
        for clip in track.get("clips") or []:
            if isinstance(clip, dict):
                clips.append(
                    {**clip, "track_type": clip.get("track_type") or track_type}
                )
    return clips


def _clip_asset_candidates(clip: dict[str, Any]) -> list[ClipAssetCandidate]:
    clip_id = str(clip.get("clip_id") or "")
    if not clip_id:
        return []
    source_ref = _source_ref(clip)
    candidates: list[ClipAssetCandidate] = []
    candidates.extend(_asset_ref_candidates(clip, "asset_ref", source_ref))
    for key, role in (
        ("start_frame_asset_ref", "start_frame"),
        ("end_frame_asset_ref", "end_frame"),
        ("storyboard_image_asset_ref", "storyboard_image"),
        ("storyboard_video_asset_ref", "storyboard_video"),
    ):
        candidates.extend(_asset_ref_candidates(clip, key, source_ref, role=role))
    direct_video = _string_value(
        clip.get("video_url")
        or clip.get("video_oss_url")
        or clip.get("result_video_url")
    )
    if direct_video and not candidates:
        candidates.append(
            _candidate(
                clip_id=clip_id,
                track_type=_track_type(clip),
                asset_ref={"url": direct_video, "kind": "direct_video"},
                source_ref=source_ref,
            )
        )
    return candidates


def _asset_ref_candidates(
    clip: dict[str, Any],
    key: str,
    source_ref: dict[str, Any],
    *,
    role: str | None = None,
) -> list[ClipAssetCandidate]:
    asset_ref = clip.get(key)
    if not isinstance(asset_ref, dict):
        return []
    candidate = _candidate(
        clip_id=str(clip.get("clip_id")),
        track_type=_track_type(clip),
        asset_ref=asset_ref,
        source_ref={**source_ref, "asset_ref_key": key},
        role=role,
    )
    if not _has_asset_locator(candidate):
        return []
    return [candidate]


def _candidate(
    *,
    clip_id: str,
    track_type: str | None,
    asset_ref: dict[str, Any],
    source_ref: dict[str, Any],
    role: str | None = None,
) -> ClipAssetCandidate:
    asset_role = role or _asset_role(asset_ref, track_type)
    return ClipAssetCandidate(
        clip_id=clip_id,
        track_type=track_type,
        asset_role=asset_role,
        asset_type=_asset_type(asset_ref, track_type),
        origin=_origin(asset_ref),
        media_asset_id=_maybe_int(
            asset_ref.get("media_asset_id")
            or asset_ref.get("asset_id")
            or asset_ref.get("video_asset_id")
            or asset_ref.get("audio_asset_id")
            or asset_ref.get("image_asset_id")
        ),
        file_url=_string_value(
            asset_ref.get("file_url")
            or asset_ref.get("url")
            or asset_ref.get("video_url")
            or asset_ref.get("video_oss_url")
            or asset_ref.get("image_url")
        ),
        file_path=_string_value(asset_ref.get("file_path")),
        object_key=_string_value(asset_ref.get("object_key")),
        mime_type=_mime_type(asset_ref, track_type),
        duration_ms=_maybe_int(asset_ref.get("duration_ms")),
        source="timeline_spec",
        source_ref={**source_ref, "asset_ref": asset_ref, "asset_role": asset_role},
    )


def _asset_role(asset_ref: dict[str, Any], track_type: str | None) -> str:
    kind = str(asset_ref.get("kind") or "").lower()
    if "episode_audio" in kind or track_type == "dialogue":
        return "source_audio"
    if "start" in kind and "frame" in kind:
        return "start_frame"
    if "end" in kind and "frame" in kind:
        return "end_frame"
    if "storyboard" in kind and "image" in kind:
        return "storyboard_image"
    if "storyboard" in kind and "video" in kind:
        return "storyboard_video"
    if track_type == "video":
        return "generated_video"
    return f"{track_type or 'clip'}_asset"


def _asset_type(asset_ref: dict[str, Any], track_type: str | None) -> str:
    kind = str(asset_ref.get("kind") or "").lower()
    if "audio" in kind or track_type == "dialogue":
        return "audio"
    if "image" in kind or "frame" in kind:
        return "image"
    if track_type == "subtitle":
        return "subtitle"
    return "video"


def _origin(asset_ref: dict[str, Any]) -> str:
    kind = str(asset_ref.get("kind") or "").lower()
    if "legacy" in kind:
        return "legacy"
    if "episode_audio" in kind:
        return "imported"
    if "render" in kind:
        return "rendered"
    return "timeline_spec"


def _mime_type(asset_ref: dict[str, Any], track_type: str | None) -> str | None:
    value = _string_value(asset_ref.get("mime_type"))
    if value:
        return value
    asset_type = _asset_type(asset_ref, track_type)
    return {"audio": "audio/mpeg", "video": "video/mp4", "image": "image/png"}.get(
        asset_type
    )


def _source_ref(clip: dict[str, Any]) -> dict[str, Any]:
    return {
        "clip_id": clip.get("clip_id"),
        "track_type": clip.get("track_type"),
        "scene_id": clip.get("scene_id"),
        "beat_id": clip.get("beat_id"),
        "source": clip.get("source") if isinstance(clip.get("source"), dict) else None,
        "source_refs": (
            clip.get("source_refs")
            if isinstance(clip.get("source_refs"), dict)
            else None
        ),
    }


def _track_type(clip: dict[str, Any]) -> str | None:
    return str(clip.get("track_type") or "") or None


def _string_value(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _maybe_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _has_asset_locator(candidate: ClipAssetCandidate) -> bool:
    return bool(
        candidate.media_asset_id
        or candidate.file_url
        or candidate.file_path
        or candidate.object_key
    )
