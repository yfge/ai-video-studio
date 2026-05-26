"""Resolve Timeline dialogue audio for render composition."""

from __future__ import annotations

from typing import Any

from app.models.timeline import Timeline
from app.services.render.timeline_render_types import TimelineAudioTrack


def resolve_timeline_audio_track(timeline: Timeline) -> TimelineAudioTrack | None:
    spec = timeline.spec if isinstance(timeline.spec, dict) else {}
    source_audio = _source_episode_audio_url(spec)
    if source_audio:
        return TimelineAudioTrack(
            url=source_audio,
            source="timeline.source.episode_audio",
            clip_count=len(_dialogue_clips(spec)),
        )

    dialogue_clips = _dialogue_clips(spec)
    dialogue_urls = [_clip_audio_url(clip) for clip in dialogue_clips]
    unique_urls = {url for url in dialogue_urls if url}
    if dialogue_clips and all(dialogue_urls) and len(unique_urls) == 1:
        return TimelineAudioTrack(
            url=next(iter(unique_urls)),
            source="timeline.dialogue.asset_ref",
            clip_count=len(dialogue_clips),
        )
    return None


def _source_episode_audio_url(spec: dict[str, Any]) -> str | None:
    source = spec.get("source")
    if not isinstance(source, dict):
        return None
    episode_audio = source.get("episode_audio")
    if not isinstance(episode_audio, dict):
        return None
    return _string_value(
        episode_audio.get("oss_url")
        or episode_audio.get("audio_url")
        or episode_audio.get("file_url")
        or episode_audio.get("url")
    )


def _dialogue_clips(spec: dict[str, Any]) -> list[dict[str, Any]]:
    clips: list[dict[str, Any]] = []
    for track in spec.get("tracks") or []:
        if not isinstance(track, dict):
            continue
        track_type = str(track.get("track_type") or track.get("type") or "")
        if track_type != "dialogue":
            continue
        clips.extend(
            item for item in track.get("clips") or [] if isinstance(item, dict)
        )
    return clips


def _clip_audio_url(clip: dict[str, Any]) -> str | None:
    asset_ref = clip.get("asset_ref")
    if not isinstance(asset_ref, dict):
        return None
    return _string_value(
        asset_ref.get("oss_url")
        or asset_ref.get("audio_url")
        or asset_ref.get("file_url")
        or asset_ref.get("url")
    )


def _string_value(value: Any) -> str | None:
    if isinstance(value, str) and value.strip().startswith(("http://", "https://")):
        return value.strip()
    return None
