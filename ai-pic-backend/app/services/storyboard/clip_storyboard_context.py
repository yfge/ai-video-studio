"""Bind Timeline clip storyboard tasks to story visual context."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from app.core.validators.character_registry import (
    normalize_character_name_token,
    normalize_to_registered_or_generic,
)
from app.models.script import Episode
from app.models.timeline import Timeline
from sqlalchemy.orm import Session

from .clip_storyboard_environment_context import (
    build_clip_storyboard_environment_context,
)
from .storyboard_audio_character_visuals import load_story_character_visuals
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
) -> ClipStoryboardContext:
    manual_refs = dedupe_strs(request_reference_images or [])
    story_id = _story_id(db, timeline)
    script_id = _maybe_int(getattr(timeline, "script_id", None))
    warnings: list[str] = []

    bound_context: dict[str, Any] = {
        "characters": [],
        "warnings": warnings,
    }
    reference_images = list(manual_refs)

    if story_id:
        visuals, alias_to_canonical = load_story_character_visuals(
            db, story_id=story_id
        )
        matched_names = _matched_character_names(
            timeline=timeline,
            clip=clip,
            panels=panels,
            visuals=visuals,
            alias_to_canonical=alias_to_canonical,
        )
        if matched_names:
            characters = []
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
            bound_context["characters"] = characters
        elif len(visuals) > 1:
            warnings.append("character_context_not_resolved")

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


def _matched_character_names(
    *,
    timeline: Timeline,
    clip: dict[str, Any],
    panels: Sequence[dict[str, Any]],
    visuals: dict[str, Any],
    alias_to_canonical: dict[str, str],
) -> list[str]:
    if not visuals:
        return []

    matched: list[str] = []
    for value in _explicit_character_values(timeline, clip):
        _append_character_match(matched, value, alias_to_canonical, visuals)

    text = _context_text(clip, panels)
    if text and alias_to_canonical:
        for alias, canonical in alias_to_canonical.items():
            if (
                alias
                and alias in text
                and canonical in visuals
                and canonical not in matched
            ):
                matched.append(canonical)

    if not matched and len(visuals) == 1:
        matched.append(next(iter(visuals)))
    return matched


def _explicit_character_values(timeline: Timeline, clip: dict[str, Any]) -> list[Any]:
    values: list[Any] = []
    for key in (
        "speaker_name",
        "character",
        "character_name",
        "characters",
        "characters_involved",
    ):
        values.extend(_flatten_values(clip.get(key)))

    scene_id = clip.get("scene_id")
    beat_id = clip.get("beat_id")
    spec = timeline.spec if isinstance(timeline.spec, dict) else {}
    for track in spec.get("tracks") or []:
        if not isinstance(track, dict):
            continue
        track_type = track.get("track_type") or track.get("type")
        if track_type != "dialogue":
            continue
        for dialogue in track.get("clips") or []:
            if not isinstance(dialogue, dict):
                continue
            if not _same_source(dialogue.get("scene_id"), scene_id):
                continue
            if beat_id is not None and not _same_source(
                dialogue.get("beat_id"), beat_id
            ):
                continue
            for key in ("speaker_name", "character", "character_name", "speaker"):
                values.extend(_flatten_values(dialogue.get(key)))
    return values


def _append_character_match(
    matched: list[str],
    value: Any,
    alias_to_canonical: dict[str, str],
    visuals: dict[str, Any],
) -> None:
    token = normalize_character_name_token(str(value) if value is not None else "")
    if not token:
        return
    canonical = normalize_to_registered_or_generic(
        token,
        alias_to_canonical=alias_to_canonical,
    )
    if canonical in visuals and canonical not in matched:
        matched.append(canonical)


def _context_text(clip: dict[str, Any], panels: Sequence[dict[str, Any]]) -> str:
    values: list[str] = []
    for key in (
        "text",
        "label",
        "prompt",
        "ai_prompt",
        "description",
        "speaker_name",
    ):
        value = clip.get(key)
        if isinstance(value, str):
            values.append(value)

    source_refs = clip.get("source_refs")
    shot_plan = (
        source_refs.get("timeline_shot_plan") if isinstance(source_refs, dict) else None
    )
    if isinstance(shot_plan, dict):
        for value in shot_plan.values():
            if isinstance(value, str):
                values.append(value)

    for panel in panels:
        if not isinstance(panel, dict):
            continue
        for key in ("visual_prompt", "video_prompt", "storyboard_panel_prompt"):
            value = panel.get(key)
            if isinstance(value, str):
                values.append(value)
    return "\n".join(values)


def _flatten_values(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, dict):
        return list(value.values())
    if isinstance(value, (list, tuple, set)):
        flattened: list[Any] = []
        for item in value:
            flattened.extend(_flatten_values(item))
        return flattened
    return [value]


def _same_source(left: Any, right: Any) -> bool:
    return str(left) == str(right)


def _maybe_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None and str(value).strip() else None
    except (TypeError, ValueError):
        return None
