from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.models.script import Episode, Script
from app.models.timeline import Timeline
from app.repositories.timeline_repository import TimelineRepository
from app.services.timeline_spec_builder import (
    audio_timeline_version,
    build_timeline_spec_from_audio_timeline,
)
from app.services.timeline_storyboard_spec_builder import (
    build_timeline_spec_from_storyboard_frames,
)
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class TimelineImportResult:
    timeline: Timeline
    action: str


def import_audio_timeline_to_timeline_spec(
    db: Session,
    *,
    episode: Episode,
    script: Script,
    audio_timeline: dict[str, Any] | None = None,
    overwrite: bool = False,
    user_id: int | None = None,
) -> TimelineImportResult:
    """Create or update the episode Timeline Spec v1 from audio_timeline beats."""
    timeline_payload = audio_timeline or _episode_audio_timeline(episode)
    if not isinstance(timeline_payload, dict):
        raise RuntimeError("episode_audio_timeline_not_found")
    if timeline_payload.get("script_id") != script.id:
        raise RuntimeError("audio_timeline_script_mismatch")

    repo = TimelineRepository(db)
    existing = repo.get_latest_for_episode_script(
        episode_id=episode.id,
        script_id=script.id,
    )
    if existing is not None and not overwrite:
        return TimelineImportResult(timeline=existing, action="skipped")

    next_version = 1 if existing is None else (existing.version or 0) + 1
    source_version = audio_timeline_version(timeline_payload)
    spec = _build_import_spec(
        episode=episode,
        script=script,
        audio_timeline=timeline_payload,
        version=next_version,
        source_version=source_version,
    )

    if existing is None:
        timeline = repo.create(
            episode_id=episode.id,
            episode_business_id=episode.business_id,
            script_id=script.id,
            script_business_id=script.business_id,
            title=f"{episode.title} Timeline",
            status="draft",
            spec=spec,
            version=next_version,
            source_audio_timeline_version=source_version,
            created_by=user_id,
            updated_by=user_id,
        )
        db.flush()
        timeline.spec = {**(timeline.spec or {}), "timeline_id": timeline.id}
        action = "created"
    else:
        spec["timeline_id"] = existing.id
        timeline = repo.update(
            existing,
            spec=spec,
            version=next_version,
            source_audio_timeline_version=source_version,
            updated_by=user_id,
        )
        action = "updated"

    db.commit()
    db.refresh(timeline)
    return TimelineImportResult(timeline=timeline, action=action)


def _episode_audio_timeline(episode: Episode) -> dict[str, Any] | None:
    meta = episode.extra_metadata if isinstance(episode.extra_metadata, dict) else {}
    timeline = meta.get("audio_timeline") if isinstance(meta, dict) else None
    return timeline if isinstance(timeline, dict) else None


def _build_import_spec(
    *,
    episode: Episode,
    script: Script,
    audio_timeline: dict[str, Any],
    version: int,
    source_version: int | None,
) -> dict[str, Any]:
    try:
        return build_timeline_spec_from_audio_timeline(
            episode=episode,
            script=script,
            audio_timeline=audio_timeline,
            version=version,
        )
    except RuntimeError as exc:
        if str(exc) != "audio_timeline_beats_not_monotonic":
            raise
        frames = _legacy_storyboard_frames(script)
        if not frames:
            raise
        return build_timeline_spec_from_storyboard_frames(
            episode=episode,
            script=script,
            storyboard_frames=frames,
            version=version,
            source_audio_timeline_version=source_version,
        )


def _legacy_storyboard_frames(script: Script) -> list[dict[str, Any]]:
    extra = script.extra_metadata if isinstance(script.extra_metadata, dict) else {}
    storyboard = extra.get("storyboard") if isinstance(extra, dict) else None
    frames = storyboard.get("frames") if isinstance(storyboard, dict) else None
    return [frame for frame in frames or [] if isinstance(frame, dict)]
