"""Resolve a Timeline that can safely accept a generated storyboard sheet."""

from __future__ import annotations

from typing import Any

from app.repositories.timeline_repository import TimelineRepository

from .grid_storyboard_sheet_payload import (
    grid_payload_matches_current_timeline,
    maybe_int,
)


def compatible_storyboard_timeline_or_raise(
    timelines: TimelineRepository,
    timeline_id: int,
    payload: dict[str, Any],
    *,
    for_update: bool = False,
):
    timeline = (
        timelines.get_by_id_for_update(timeline_id)
        if for_update
        else timelines.get_by_id(timeline_id)
    )
    if timeline is None or timeline.is_deleted:
        raise RuntimeError("timeline_not_found")
    expected_version = maybe_int(payload.get("expected_version"))
    if expected_version is not None and timeline.version == expected_version:
        return timeline
    if not grid_payload_matches_current_timeline(timeline, payload):
        raise RuntimeError("timeline version conflict")
    return timeline
