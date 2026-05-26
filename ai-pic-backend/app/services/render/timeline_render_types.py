"""Shared render DTOs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TimelineClipVideo:
    """Resolved video source for one Timeline video clip."""

    clip_id: str
    url: str
    duration_seconds: float
    scene_id: Any = None
    scene_number: Any = None
    start_ms: int | None = None
    end_ms: int | None = None
    source: str = "timeline"


@dataclass(frozen=True)
class TimelineSubtitleCue:
    """Resolved subtitle cue for Timeline rendering."""

    text: str
    start_ms: int
    end_ms: int
    clip_id: str


@dataclass(frozen=True)
class TimelineAudioTrack:
    """Resolved source audio for Timeline rendering."""

    url: str
    source: str
    clip_count: int
