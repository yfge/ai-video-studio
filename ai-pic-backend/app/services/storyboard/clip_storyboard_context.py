"""Bind Timeline clip storyboard tasks to story visual context."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from app.models.script import Episode
from app.models.timeline import Timeline
from sqlalchemy.orm import Session

from .clip_storyboard_character_context import build_clip_storyboard_character_context
from .clip_storyboard_environment_context import (
    build_clip_storyboard_environment_context,
)
from .storyboard_audio_context_utils import dedupe_strs


@dataclass(frozen=True, slots=True)
class ClipStoryboardContext:
    bound_context: dict[str, Any]
    reference_images: list[str]
    panels: list[dict[str, Any]]


def build_clip_storyboard_context(
    db: Session,
    *,
    timeline: Timeline,
    clip: dict[str, Any],
    panels: Sequence[dict[str, Any]],
    request_reference_images: Sequence[str] | None,
    request_character_virtual_ip_ids: Sequence[int] | None = None,
) -> ClipStoryboardContext:
    manual_refs = dedupe_strs(request_reference_images or [])
    story_id = _story_id(db, timeline)
    episode_id = _maybe_int(getattr(timeline, "episode_id", None))
    script_id = _maybe_int(getattr(timeline, "script_id", None))
    warnings: list[str] = []

    bound_context: dict[str, Any] = {
        "characters": [],
        "warnings": warnings,
    }
    reference_images = list(manual_refs)

    character_context = build_clip_storyboard_character_context(
        db,
        timeline=timeline,
        clip=clip,
        panels=panels,
        story_id=story_id,
        episode_id=episode_id,
        request_character_virtual_ip_ids=request_character_virtual_ip_ids,
    )
    bound_context["characters"] = character_context.characters
    reference_images.extend(character_context.reference_images)
    warnings.extend(character_context.warnings)

    env_context = build_clip_storyboard_environment_context(
        db,
        clip=clip,
        script_id=script_id,
    )
    if env_context:
        bound_context["environment"] = env_context
        env_url = env_context.get("reference_url")
        if isinstance(env_url, str) and env_url.strip():
            reference_images.append(env_url.strip())

    reference_images = dedupe_strs(reference_images)
    panels_with_context = [
        {**panel, "bound_context": bound_context} for panel in panels
    ]
    return ClipStoryboardContext(
        bound_context=bound_context,
        reference_images=reference_images,
        panels=panels_with_context,
    )


def _story_id(db: Session, timeline: Timeline) -> int | None:
    episode = getattr(timeline, "episode", None)
    if not isinstance(episode, Episode):
        episode_id = _maybe_int(getattr(timeline, "episode_id", None))
        episode = db.get(Episode, episode_id) if episode_id else None
    return _maybe_int(getattr(episode, "story_id", None)) if episode else None


def _maybe_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None and str(value).strip() else None
    except (TypeError, ValueError):
        return None
