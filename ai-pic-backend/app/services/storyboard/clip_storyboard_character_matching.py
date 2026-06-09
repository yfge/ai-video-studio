"""Match clip storyboard character signals to VirtualIP visual anchors."""

from __future__ import annotations

from typing import Any, Sequence

from app.core.validators.character_registry import (
    normalize_character_name_token,
    normalize_to_registered_or_generic,
)
from app.models.timeline import Timeline

from .storyboard_audio_character_visuals import StoryCharacterVisual


def matched_character_names(
    *,
    timeline: Timeline,
    clip: dict[str, Any],
    panels: Sequence[dict[str, Any]],
    visuals: dict[str, StoryCharacterVisual],
    alias_to_canonical: dict[str, str],
    request_character_virtual_ip_ids: Sequence[int] | None,
    warnings: list[str],
) -> list[str]:
    if not visuals:
        return []

    by_virtual_ip_id = {
        int(visual.virtual_ip_id): canonical
        for canonical, visual in visuals.items()
        if _maybe_int(visual.virtual_ip_id) is not None
    }
    explicit_ids = _dedupe_ints(
        [
            *_extract_ints(request_character_virtual_ip_ids),
            *_explicit_virtual_ip_ids(timeline, clip),
        ]
    )
    if explicit_ids:
        matched_by_id = [
            by_virtual_ip_id[vip_id]
            for vip_id in explicit_ids
            if vip_id in by_virtual_ip_id
        ]
        if len(matched_by_id) < len(explicit_ids):
            warnings.append("character_ip_context_not_resolved")
        return _dedupe_names(matched_by_id)

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


def _explicit_virtual_ip_ids(timeline: Timeline, clip: dict[str, Any]) -> list[int]:
    ids: list[int] = []
    for source in _same_beat_contexts(timeline, clip):
        for key in ("virtual_ip_id", "virtual_ip_ids", "character_ids"):
            ids.extend(_extract_ints(source.get(key)))
        source_refs = source.get("source_refs")
        if isinstance(source_refs, dict):
            for key in ("virtual_ip_id", "virtual_ip_ids", "character_ids"):
                ids.extend(_extract_ints(source_refs.get(key)))
        for key in ("character", "characters"):
            ids.extend(_extract_nested_virtual_ip_ids(source.get(key)))
    return _dedupe_ints(ids)


def _explicit_character_values(timeline: Timeline, clip: dict[str, Any]) -> list[Any]:
    values: list[Any] = []
    for source in _same_beat_contexts(timeline, clip):
        for key in (
            "speaker_name",
            "character",
            "character_name",
            "characters",
            "characters_involved",
        ):
            values.extend(_flatten_values(source.get(key)))
        source_refs = source.get("source_refs")
        if isinstance(source_refs, dict):
            for key in ("speaker_name", "character", "character_name"):
                values.extend(_flatten_values(source_refs.get(key)))
    return values


def _same_beat_contexts(
    timeline: Timeline, clip: dict[str, Any]
) -> list[dict[str, Any]]:
    contexts = [clip]
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
            contexts.append(dialogue)
    return contexts


def _append_character_match(
    matched: list[str],
    value: Any,
    alias_to_canonical: dict[str, str],
    visuals: dict[str, StoryCharacterVisual],
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


def _extract_ints(value: Any) -> list[int]:
    ints: list[int] = []
    for item in _flatten_values(value):
        parsed = _maybe_int(item)
        if parsed is not None:
            ints.append(parsed)
    return ints


def _extract_nested_virtual_ip_ids(value: Any) -> list[int]:
    if value is None:
        return []
    if isinstance(value, dict):
        ids = _extract_ints(
            value.get("virtual_ip_id")
            or value.get("virtual_ip_ids")
            or value.get("character_ids")
        )
        for nested in ("character", "characters"):
            ids.extend(_extract_nested_virtual_ip_ids(value.get(nested)))
        return ids
    if isinstance(value, (list, tuple, set)):
        ids: list[int] = []
        for item in value:
            ids.extend(_extract_nested_virtual_ip_ids(item))
        return ids
    return []


def _dedupe_ints(values: list[int]) -> list[int]:
    deduped: list[int] = []
    for value in values:
        if value in deduped:
            continue
        deduped.append(value)
    return deduped


def _dedupe_names(names: list[str]) -> list[str]:
    deduped: list[str] = []
    for name in names:
        if name in deduped:
            continue
        deduped.append(name)
    return deduped


def _same_source(left: Any, right: Any) -> bool:
    return str(left) == str(right)


def _maybe_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None and str(value).strip() else None
    except (TypeError, ValueError):
        return None
