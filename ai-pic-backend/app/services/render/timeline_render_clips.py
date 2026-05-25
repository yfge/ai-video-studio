"""Resolve Timeline video clips into renderable video sources."""

from __future__ import annotations

from typing import Any

from app.models.timeline import Timeline
from app.repositories.timeline_repository import MediaAssetRepository
from app.services.render.timeline_render_clip_assets import (
    TimelineClipAssetVideoResolver,
)
from app.services.render.timeline_render_legacy_match import (
    find_legacy_storyboard_frame,
)
from app.services.render.timeline_render_types import TimelineClipVideo
from sqlalchemy.orm import Session


def resolve_timeline_video_clips(
    db: Session,
    timeline: Timeline,
) -> tuple[list[TimelineClipVideo], list[dict[str, Any]]]:
    resolver = TimelineClipResolver(db)
    return resolver.resolve(timeline)


class TimelineClipResolver:
    def __init__(self, db: Session):
        self.media_assets = MediaAssetRepository(db)
        self.clip_asset_videos = TimelineClipAssetVideoResolver(db)

    def resolve(
        self,
        timeline: Timeline,
    ) -> tuple[list[TimelineClipVideo], list[dict[str, Any]]]:
        spec = timeline.spec if isinstance(timeline.spec, dict) else {}
        storyboard_frames = self._storyboard_frames(timeline)
        resolved: list[TimelineClipVideo] = []
        missing: list[dict[str, Any]] = []

        for clip in self._timeline_video_clips(spec):
            clip_id = self._clip_id(clip)
            url, source = self._resolve_clip_video_url(
                timeline, clip, storyboard_frames
            )
            if not url:
                missing.append(self._missing_clip_payload(clip, clip_id))
                continue
            resolved.append(
                TimelineClipVideo(
                    clip_id=clip_id,
                    url=url,
                    duration_seconds=self._clip_duration_seconds(clip),
                    scene_id=clip.get("scene_id"),
                    scene_number=clip.get("scene_number"),
                    start_ms=self._maybe_int(clip.get("start_ms")),
                    end_ms=self._maybe_int(clip.get("end_ms")),
                    source=source,
                )
            )
        return resolved, missing

    def _resolve_clip_video_url(
        self,
        timeline: Timeline,
        clip: dict[str, Any],
        storyboard_frames: list[dict[str, Any]],
    ) -> tuple[str | None, str]:
        clip_asset_url, clip_asset_source = self.clip_asset_videos.resolve(
            timeline=timeline,
            clip_id=self._clip_id(clip),
        )
        if clip_asset_url:
            return clip_asset_url, clip_asset_source

        direct = self._clip_direct_video_url(clip)
        if direct:
            return direct, "timeline_clip"

        for frame in storyboard_frames:
            if self._frame_matches_clip(frame, clip):
                url = self._frame_video_url(frame)
                if url:
                    return url, "storyboard_frame"
        legacy_frame = find_legacy_storyboard_frame(clip, storyboard_frames)
        if legacy_frame:
            url = self._frame_video_url(legacy_frame)
            if url:
                return url, "legacy_storyboard_timing"
        return None, "missing"

    def _clip_direct_video_url(self, clip: dict[str, Any]) -> str | None:
        for key in ("video_url", "video_oss_url", "result_video_url", "file_url"):
            value = clip.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        asset_ref = clip.get("asset_ref")
        if isinstance(asset_ref, dict):
            for key in ("file_url", "url", "video_url", "video_oss_url", "file_path"):
                value = asset_ref.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
            asset_url = self._media_asset_url(
                self._maybe_int(
                    asset_ref.get("media_asset_id")
                    or asset_ref.get("asset_id")
                    or asset_ref.get("video_asset_id")
                )
            )
            if asset_url:
                return asset_url

        for key in ("media_asset_id", "asset_id", "video_asset_id"):
            asset_url = self._media_asset_url(self._maybe_int(clip.get(key)))
            if asset_url:
                return asset_url
        return None

    def _media_asset_url(self, asset_id: int | None) -> str | None:
        if not asset_id:
            return None
        asset = self.media_assets.get_by_id(asset_id)
        if asset is None or asset.is_deleted:
            return None
        return asset.file_url or asset.file_path

    @staticmethod
    def _timeline_video_clips(spec: dict[str, Any]) -> list[dict[str, Any]]:
        clips: list[dict[str, Any]] = []
        tracks = spec.get("tracks")
        if not isinstance(tracks, list):
            return clips
        for track in tracks:
            if not isinstance(track, dict):
                continue
            track_type = str(track.get("track_type") or track.get("type") or "")
            if track_type != "video":
                continue
            raw_clips = track.get("clips")
            if isinstance(raw_clips, list):
                clips.extend(item for item in raw_clips if isinstance(item, dict))
        return clips

    @staticmethod
    def _storyboard_frames(timeline: Timeline) -> list[dict[str, Any]]:
        script = getattr(timeline, "script", None)
        storyboard = (
            (script.extra_metadata or {}).get("storyboard")
            if script is not None and isinstance(script.extra_metadata, dict)
            else None
        )
        frames = storyboard.get("frames") if isinstance(storyboard, dict) else None
        return [frame for frame in frames or [] if isinstance(frame, dict)]

    @staticmethod
    def _frame_matches_clip(
        frame: dict[str, Any],
        clip: dict[str, Any],
    ) -> bool:
        clip_ids = {
            TimelineClipResolver._clip_id(clip),
            str(clip.get("frame_id") or ""),
            str(clip.get("storyboard_frame_id") or ""),
        }
        source = clip.get("source")
        if isinstance(source, dict):
            clip_ids.add(str(source.get("storyboard_frame_id") or ""))
        source_refs = clip.get("source_refs")
        if isinstance(source_refs, dict):
            clip_ids.add(str(source_refs.get("storyboard_frame_id") or ""))

        frame_ids = {
            str(frame.get("timeline_clip_id") or ""),
            str(frame.get("frame_id") or ""),
            str(frame.get("id") or ""),
        }
        return bool((clip_ids - {""}) & (frame_ids - {""}))

    @staticmethod
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

    @staticmethod
    def _missing_clip_payload(
        clip: dict[str, Any],
        clip_id: str,
    ) -> dict[str, Any]:
        return {
            "clip_id": clip_id,
            "scene_id": clip.get("scene_id"),
            "scene_number": clip.get("scene_number"),
            "start_ms": TimelineClipResolver._maybe_int(clip.get("start_ms")),
            "end_ms": TimelineClipResolver._maybe_int(clip.get("end_ms")),
            "reason": "missing_video_url",
        }

    @staticmethod
    def _clip_duration_seconds(clip: dict[str, Any]) -> float:
        start_ms = TimelineClipResolver._maybe_int(clip.get("start_ms"))
        end_ms = TimelineClipResolver._maybe_int(clip.get("end_ms"))
        if start_ms is not None and end_ms is not None and end_ms > start_ms:
            return max((end_ms - start_ms) / 1000, 0.1)
        duration_ms = TimelineClipResolver._maybe_int(clip.get("duration_ms"))
        if duration_ms and duration_ms > 0:
            return max(duration_ms / 1000, 0.1)
        duration_seconds = TimelineClipResolver._maybe_float(
            clip.get("duration_seconds")
        )
        if duration_seconds and duration_seconds > 0:
            return max(duration_seconds, 0.1)
        return 3.0

    @staticmethod
    def _clip_id(clip: dict[str, Any]) -> str:
        return str(clip.get("clip_id") or clip.get("id") or "unknown")

    @staticmethod
    def _maybe_int(value: Any) -> int | None:
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _maybe_float(value: Any) -> float | None:
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None
