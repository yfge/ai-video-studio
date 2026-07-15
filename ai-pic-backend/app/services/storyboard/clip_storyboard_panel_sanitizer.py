"""Sanitize inherited shot-plan text against authoritative clip bindings."""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

from .grid_storyboard_prompt_layers import build_panel_prompt

_SECTION_PATTERN = re.compile(
    r"(?:^|\s)(Plot|Dialogue|Character anchor|Camera|Action|Style|Duration|"
    r"Composition geometry|Motion timeline|Emotional landing):\s*",
    flags=re.IGNORECASE,
)
_DROPPED_VIDEO_SECTIONS = {"character anchor", "style"}


def sanitize_clip_storyboard_panels(
    panels: Sequence[Mapping[str, Any]],
    *,
    style: str | None,
) -> list[dict[str, Any]]:
    """Return panels whose identity/style text agrees with bound context."""

    sanitized: list[dict[str, Any]] = []
    for panel in panels:
        updated = dict(panel)
        updated["source_refs"] = _source_refs_without_inherited_shot_plan(
            panel.get("source_refs")
        )
        names = _bound_character_names(panel)
        raw_video_prompt = str(panel.get("video_prompt") or "").strip()
        plot = _section_value(raw_video_prompt, "plot")
        updated["motion_timeline"] = _sanitize_motion_timeline(
            panel.get("motion_timeline"), names
        )
        updated["visual_prompt"] = _visual_prompt(
            panel,
            plot=plot,
            names=names,
            motion_timeline=updated["motion_timeline"],
        )
        updated["video_prompt"] = _video_prompt(raw_video_prompt, names)
        for key in (
            "direction_anchor",
            "composition_geometry",
            "emotional_landing",
        ):
            updated[key] = _replace_identity_aliases(panel.get(key), names)
        updated["aesthetic_reference"] = _style_safe_aesthetic(
            panel.get("aesthetic_reference"), style
        )
        updated["storyboard_panel_prompt"] = build_panel_prompt(updated)
        sanitized.append(updated)
    return sanitized


def _source_refs_without_inherited_shot_plan(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    source_refs = dict(value)
    source_refs.pop("timeline_shot_plan", None)
    return source_refs


def _visual_prompt(
    panel: Mapping[str, Any],
    *,
    plot: str,
    names: list[str],
    motion_timeline: list[dict[str, Any]],
) -> str:
    raw_visual = str(panel.get("visual_prompt") or "").strip()
    base = plot if plot and any(name in plot for name in names) else raw_visual
    base = re.split(r"\s+Moment\s+\d+\s+at\s+", base, maxsplit=1)[0].strip()
    base = _replace_identity_aliases(base, names)
    if not motion_timeline:
        return base
    panel_index = _maybe_int(panel.get("panel_index")) or 1
    point = motion_timeline[min(panel_index - 1, len(motion_timeline) - 1)]
    action = str(point.get("action") or "").strip()
    at_ms = point.get("at_ms")
    if not action:
        return base
    return f"{base} Moment {panel_index} at {at_ms}ms: {action}".strip()


def _video_prompt(value: str, names: list[str]) -> str:
    sections = _sections(value)
    if not sections:
        return _replace_identity_aliases(value, names)
    kept = [
        f"{label}: {_replace_identity_aliases(content, names)}"
        for label, content in sections
        if label.lower() not in _DROPPED_VIDEO_SECTIONS and content
    ]
    return " ".join(kept)


def _sections(value: str) -> list[tuple[str, str]]:
    matches = list(_SECTION_PATTERN.finditer(value))
    sections: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(value)
        sections.append((match.group(1), value[match.end() : end].strip()))
    return sections


def _section_value(value: str, requested_label: str) -> str:
    for label, content in _sections(value):
        if label.lower() == requested_label.lower():
            return content
    return ""


def _sanitize_motion_timeline(
    value: Any,
    names: list[str],
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    points: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        points.append(
            {
                **item,
                "action": _replace_identity_aliases(item.get("action"), names),
            }
        )
    return points


def _bound_character_names(panel: Mapping[str, Any]) -> list[str]:
    context = panel.get("bound_context")
    characters = context.get("characters") if isinstance(context, Mapping) else None
    if not isinstance(characters, list):
        return []
    return [
        str(character.get("name")).strip()
        for character in characters
        if isinstance(character, Mapping) and character.get("name")
    ]


def _replace_identity_aliases(value: Any, names: list[str]) -> str:
    text = str(value or "").strip()
    if not text or not names:
        return text
    aliases: list[tuple[str, str]] = []
    if names:
        aliases.extend(
            (alias, names[0])
            for alias in (
                "a confident middle-aged man",
                "confident middle-aged man",
                "the middle-aged man",
                "a middle-aged man",
                "middle-aged man",
                "the older man",
                "older man",
            )
        )
    if len(names) > 1:
        aliases.extend(
            (alias, names[1])
            for alias in (
                "a younger, slightly awkward man",
                "younger, slightly awkward man",
                "the younger man",
                "a younger man",
                "younger man",
                "the young man",
                "young man",
            )
        )
        aliases.extend(
            [
                ("two subjects", f"{names[0]} and {names[1]}"),
                ("two men", f"{names[0]} and {names[1]}"),
                ("both", f"{names[0]} and {names[1]}"),
            ]
        )
    for alias, replacement in aliases:
        text = re.sub(
            rf"(?<!\w){re.escape(alias)}(?!\w)",
            replacement,
            text,
            flags=re.IGNORECASE,
        )
    return text


def _style_safe_aesthetic(value: Any, style: str | None) -> str:
    text = str(value or "").strip()
    lowered = text.lower()
    normalized_style = str(style or "").strip().lower()
    conflicts: tuple[str, ...] = ()
    if normalized_style == "live_action":
        conflicts = ("pixar", "cartoon", "animation", "animated", "2d", "3d")
    elif normalized_style == "3d_cartoon":
        conflicts = ("photoreal", "live action", "live-action", "2d")
    elif normalized_style == "2d_cartoon":
        conflicts = ("photoreal", "live action", "live-action", "3d")
    return "" if any(term in lowered for term in conflicts) else text


def _maybe_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None
