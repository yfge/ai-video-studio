"""Resolve Timeline subtitle clips for render composition."""

from __future__ import annotations

from typing import Any

from app.models.timeline import Timeline
from app.services.render.timeline_render_types import TimelineSubtitleCue


def resolve_timeline_subtitle_cues(timeline: Timeline) -> list[TimelineSubtitleCue]:
    spec = timeline.spec if isinstance(timeline.spec, dict) else {}
    cues: list[TimelineSubtitleCue] = []
    for clip in _subtitle_clips(spec):
        text = _clip_text(clip)
        start_ms = _maybe_int(clip.get("start_ms"))
        end_ms = _maybe_int(clip.get("end_ms"))
        if not text or start_ms is None or end_ms is None or end_ms <= start_ms:
            continue
        cues.append(
            TimelineSubtitleCue(
                text=text,
                start_ms=start_ms,
                end_ms=end_ms,
                clip_id=str(clip.get("clip_id") or clip.get("id") or "unknown"),
            )
        )
    return cues


def _subtitle_clips(spec: dict[str, Any]) -> list[dict[str, Any]]:
    clips: list[dict[str, Any]] = []
    for track in spec.get("tracks") or []:
        if not isinstance(track, dict):
            continue
        track_type = str(track.get("track_type") or track.get("type") or "")
        if track_type != "subtitle":
            continue
        clips.extend(
            item for item in track.get("clips") or [] if isinstance(item, dict)
        )
    return clips


def _clip_text(clip: dict[str, Any]) -> str:
    text = clip.get("text") or clip.get("subtitle") or clip.get("content")
    if isinstance(text, str) and text.strip():
        return text.strip()
    refs = clip.get("source_refs")
    dialogue = refs.get("dialogue") if isinstance(refs, dict) else None
    if not isinstance(dialogue, list):
        return ""
    lines = [
        f"{item.get('speaker')}: {item.get('line')}"
        for item in dialogue
        if isinstance(item, dict) and item.get("speaker") and item.get("line")
    ]
    return "\n".join(lines)


def _maybe_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None
