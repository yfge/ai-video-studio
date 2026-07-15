"""Deprecated compatibility imports for audio Timeline helpers.

Canonical implementations live in ``episode_timeline_beats`` and
``storyboard_from_timeline``. Application code must import those modules
directly; this module remains only for external import compatibility.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Sequence

from app.models.script import Episode, Script
from app.models.story_structure import Scene, SceneBeat
from app.services.storyboard.frame_duration_splitter import (
    DEFAULT_MAX_DURATION_SECONDS,
    DEFAULT_MIN_DURATION_SECONDS,
)
from sqlalchemy.orm import Session


def utc_now_iso() -> str:
    """Return the current UTC time for legacy callers."""

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_episode_timeline_beats(
    *,
    scenes: Sequence[Scene],
    beats_by_scene_id: dict[int, Sequence[SceneBeat]],
) -> tuple[list[dict[str, Any]], int]:
    """Delegate legacy imports to the canonical episode beat builder."""

    from app.services.audio.episode_timeline_beats import (
        build_episode_timeline_beats as canonical_builder,
    )

    return canonical_builder(
        scenes=scenes,
        beats_by_scene_id=beats_by_scene_id,
    )


def build_storyboard_frames_from_audio_timeline(
    *,
    audio_timeline: dict[str, Any],
    min_pause_duration_ms: int = 1500,
) -> list[dict[str, Any]]:
    """Delegate legacy imports to the canonical support-view builder."""

    from app.services.audio.storyboard_from_timeline import (
        build_storyboard_frames_from_audio_timeline as canonical_builder,
    )

    return canonical_builder(
        audio_timeline=audio_timeline,
        min_pause_duration_ms=min_pause_duration_ms,
    )


def generate_storyboard_from_episode_audio_timeline(
    db: Session,
    *,
    script: Script,
    episode: Episode,
    overwrite_existing: bool = False,
    min_pause_duration_ms: int = 1500,
    max_frame_duration_seconds: float = DEFAULT_MAX_DURATION_SECONDS,
    min_frame_duration_seconds: float = DEFAULT_MIN_DURATION_SECONDS,
    adjust_durations: bool = True,
) -> dict[str, Any]:
    """Delegate persistence while preserving the deprecated call signature.

    The three duration-adjustment arguments are accepted for import
    compatibility but intentionally ignored. Timeline/audio windows are the
    source of truth and a support view must not independently resegment them.
    """

    del max_frame_duration_seconds, min_frame_duration_seconds, adjust_durations
    from app.services.audio.storyboard_from_timeline import (
        generate_storyboard_from_episode_audio_timeline as canonical_generate,
    )

    return canonical_generate(
        db,
        script=script,
        episode=episode,
        overwrite_existing=overwrite_existing,
        min_pause_duration_ms=min_pause_duration_ms,
        legacy_support_view=True,
    )
