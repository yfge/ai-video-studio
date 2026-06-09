"""Resolve character reference bindings for clip storyboard generation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from app.models.timeline import Timeline
from sqlalchemy.orm import Session

from .clip_storyboard_character_matching import matched_character_names
from .storyboard_audio_character_visuals import (
    StoryCharacterVisual,
    load_episode_character_visuals,
    load_story_character_visuals,
)


@dataclass(frozen=True, slots=True)
class ClipStoryboardCharacterContext:
    characters: list[dict[str, Any]]
    reference_images: list[str]
    warnings: list[str]


def build_clip_storyboard_character_context(
    db: Session,
    *,
    timeline: Timeline,
    clip: dict[str, Any],
    panels: Sequence[dict[str, Any]],
    story_id: int | None,
    episode_id: int | None,
    request_character_virtual_ip_ids: Sequence[int] | None = None,
) -> ClipStoryboardCharacterContext:
    visuals, alias_to_canonical = _load_visual_registry(
        db,
        story_id=story_id,
        episode_id=episode_id,
    )
    warnings: list[str] = []
    matched_names = matched_character_names(
        timeline=timeline,
        clip=clip,
        panels=panels,
        visuals=visuals,
        alias_to_canonical=alias_to_canonical,
        request_character_virtual_ip_ids=request_character_virtual_ip_ids,
        warnings=warnings,
    )
    characters: list[dict[str, Any]] = []
    reference_images: list[str] = []
    for name in matched_names:
        visual = visuals.get(name)
        if visual is None:
            continue
        characters.append(
            {
                "name": visual.canonical_name,
                "virtual_ip_id": visual.virtual_ip_id,
                "anchor_url": visual.anchor_url,
            }
        )
        if isinstance(visual.anchor_url, str) and visual.anchor_url.strip():
            reference_images.append(visual.anchor_url.strip())
    if not matched_names and len(visuals) > 1:
        warnings.append("character_context_not_resolved")
    return ClipStoryboardCharacterContext(
        characters=characters,
        reference_images=reference_images,
        warnings=warnings,
    )


def _load_visual_registry(
    db: Session,
    *,
    story_id: int | None,
    episode_id: int | None,
) -> tuple[dict[str, StoryCharacterVisual], dict[str, str]]:
    visuals: dict[str, StoryCharacterVisual] = {}
    alias_to_canonical: dict[str, str] = {}
    if story_id:
        story_visuals, story_aliases = load_story_character_visuals(
            db, story_id=story_id
        )
        visuals.update(story_visuals)
        alias_to_canonical.update(story_aliases)
    if episode_id:
        episode_visuals, episode_aliases = load_episode_character_visuals(
            db, episode_id=episode_id
        )
        visuals.update(episode_visuals)
        alias_to_canonical.update(episode_aliases)
    return visuals, alias_to_canonical


def _maybe_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None and str(value).strip() else None
    except (TypeError, ValueError):
        return None
