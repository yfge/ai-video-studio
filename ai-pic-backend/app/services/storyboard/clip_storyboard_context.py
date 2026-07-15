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
    request_character_reference_images: Sequence[str] | None = None,
    request_environment_reference_images: Sequence[str] | None = None,
) -> ClipStoryboardContext:
    manual_refs = dedupe_strs(request_reference_images or [])
    selected_character_refs = dedupe_strs(request_character_reference_images or [])
    selected_environment_refs = dedupe_strs(request_environment_reference_images or [])
    story_id = _story_id(db, timeline)
    episode_id = _maybe_int(getattr(timeline, "episode_id", None))
    script_id = _maybe_int(getattr(timeline, "script_id", None))
    warnings: list[str] = []

    bound_context: dict[str, Any] = {
        "characters": [],
        "warnings": warnings,
    }

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
    warnings.extend(character_context.warnings)
    canonical_character_refs = dedupe_strs(character_context.reference_images)
    effective_selected_character_refs = _selected_character_refs(
        selected_character_refs,
        canonical_character_refs=canonical_character_refs,
        has_explicit_ids=bool(request_character_virtual_ip_ids),
        warnings=warnings,
    )
    ignored_character_refs = set(selected_character_refs).difference(
        effective_selected_character_refs
    )
    if ignored_character_refs:
        manual_refs = [ref for ref in manual_refs if ref not in ignored_character_refs]

    env_context = build_clip_storyboard_environment_context(
        db,
        clip=clip,
        script_id=script_id,
    )
    scene_environment_refs: list[str] = []
    if env_context:
        bound_context["environment"] = env_context
        env_url = env_context.get("reference_url")
        if isinstance(env_url, str) and env_url.strip():
            scene_environment_refs.append(env_url.strip())

    reference_images = dedupe_strs(
        [
            *canonical_character_refs,
            *effective_selected_character_refs,
            *selected_environment_refs,
            *scene_environment_refs,
            *manual_refs,
        ]
    )
    bound_context["reference_bindings"] = _reference_bindings(
        reference_images,
        characters=character_context.characters,
        requested_character_refs=effective_selected_character_refs,
        requested_environment_refs=selected_environment_refs,
        scene_environment_refs=scene_environment_refs,
        manual_refs=manual_refs,
    )
    panels_with_context = [
        {**panel, "bound_context": bound_context} for panel in panels
    ]
    return ClipStoryboardContext(
        bound_context=bound_context,
        reference_images=reference_images,
        panels=panels_with_context,
    )


def _selected_character_refs(
    requested_refs: list[str],
    *,
    canonical_character_refs: list[str],
    has_explicit_ids: bool,
    warnings: list[str],
) -> list[str]:
    if not has_explicit_ids or not canonical_character_refs:
        return requested_refs
    accepted = [ref for ref in requested_refs if ref in canonical_character_refs]
    if len(accepted) != len(requested_refs):
        warnings.append("noncanonical_character_references_ignored")
    return accepted


def _reference_bindings(
    reference_images: list[str],
    *,
    characters: list[dict[str, Any]],
    requested_character_refs: list[str],
    requested_environment_refs: list[str],
    scene_environment_refs: list[str],
    manual_refs: list[str],
) -> list[dict[str, Any]]:
    metadata: dict[str, dict[str, str]] = {}

    def register(url: str, *, role: str, label: str, source: str) -> None:
        metadata.setdefault(
            url,
            {"role": role, "label": label, "source": source},
        )

    for character in characters:
        url = character.get("anchor_url")
        if isinstance(url, str) and url.strip():
            register(
                url.strip(),
                role="character_identity",
                label=str(character.get("name") or "character").strip(),
                source="canonical_virtual_ip",
            )
    for url in requested_character_refs:
        register(
            url,
            role="character_reference",
            label="requested character",
            source="request_character_reference_images",
        )
    for url in requested_environment_refs:
        register(
            url,
            role="environment",
            label="requested environment",
            source="request_environment_reference_images",
        )
    for url in scene_environment_refs:
        register(
            url,
            role="environment",
            label="scene environment",
            source="scene_environment",
        )
    for url in manual_refs:
        register(
            url,
            role="general_reference",
            label="manual reference",
            source="request_reference_images",
        )

    return [
        {"index": index, **metadata[url], "url": url}
        for index, url in enumerate(reference_images, start=1)
    ]


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
