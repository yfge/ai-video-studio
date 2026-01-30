"""Models for audio segment planning."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlannedSegment:
    """A planned audio segment for a scene."""

    kind: str  # dialogue | action | pause
    text: str
    speaker_name: str | None = None
    emotion: str | None = None
    action: str | None = None
    timing: str | None = None  # start/mid/end (for action)
    planned_duration_ms: int | None = None
