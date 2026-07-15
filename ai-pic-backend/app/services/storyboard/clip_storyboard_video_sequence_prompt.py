"""Prompt a video model to animate a full clip storyboard sheet in order."""

from __future__ import annotations

from typing import Any, Mapping, Sequence


def build_clip_storyboard_sequence_video_prompt(
    panels: Sequence[Mapping[str, Any]],
    *,
    clip_id: str,
    duration_seconds: float,
    prompt_override: str | None = None,
) -> str:
    ordered = sorted(panels, key=_panel_index)
    if not ordered:
        raise ValueError("clip_storyboard_sequence_panels_required")
    lines = [
        (
            f"Animate the entire clip storyboard sheet as one continuous "
            f"{duration_seconds:.3f}-second Timeline clip: {clip_id}."
        ),
        (
            "Read the storyboard panels left-to-right, top-to-bottom. Each panel is "
            "a temporal action anchor in the same continuous clip, not a simultaneous collage."
        ),
        (
            "Move through every panel anchor in numeric order with natural in-between motion; "
            "do not skip, reorder, loop, or merge action beats."
        ),
        (
            "Output only one full-frame cinematic video. Never reveal or animate the sheet, "
            "gutters, borders, panel numbers, split screens, captions, or readable UI text."
        ),
        (
            "At every instant show exactly one camera view filling the complete output frame. "
            "Never stack, tile, duplicate, or place two panel moments side-by-side; transition "
            "between moments through continuous motion instead."
        ),
        (
            "Keep character identity, face, hair, wardrobe, body proportions, environment, "
            "prop continuity, eyelines, and screen direction stable across the whole clip."
        ),
    ]
    if prompt_override and prompt_override.strip():
        lines.append(f"Operator motion direction: {prompt_override.strip()}")
    else:
        narrative = _narrative_prompt(ordered)
        if narrative:
            lines.append(f"Clip narrative and motion direction: {narrative}")
    lines.append("Temporal anchors:")
    lines.extend(_panel_line(panel, ordered, duration_seconds) for panel in ordered)
    lines.append(f"End on the final panel's resolved pose by {duration_seconds:.3f}s.")
    return "\n".join(lines)


def _panel_line(
    panel: Mapping[str, Any],
    ordered: Sequence[Mapping[str, Any]],
    duration_seconds: float,
) -> str:
    index = _panel_index(panel)
    at_seconds, action = _panel_anchor(panel, ordered, duration_seconds)
    return (
        f"- Panel {index} at {at_seconds:.3f}s: {action}; "
        f"framing: {panel.get('shot_type') or 'preserve cinematic continuity'}; "
        f"composition: {panel.get('composition_geometry') or 'preserve screen direction'}."
    )


def _panel_anchor(
    panel: Mapping[str, Any],
    ordered: Sequence[Mapping[str, Any]],
    duration_seconds: float,
) -> tuple[float, str]:
    index = _panel_index(panel)
    motion = panel.get("motion_timeline")
    point = _motion_point(motion, index, len(ordered))
    action = str((point or {}).get("action") or panel.get("panel_moment") or "").strip()
    at_ms = _relative_at_ms(panel, (point or {}).get("at_ms"))
    if at_ms is None:
        denominator = max(1, len(ordered) - 1)
        at_seconds = duration_seconds * (index - 1) / denominator
    else:
        at_seconds = min(max(at_ms / 1000.0, 0.0), duration_seconds)
    return at_seconds, action or "hold the specified visual state"


def _motion_point(
    value: Any,
    panel_index: int,
    panel_count: int,
) -> Mapping[str, Any] | None:
    if not isinstance(value, list) or not value:
        return None
    point_index = round(
        (max(1, panel_index) - 1) * (len(value) - 1) / max(panel_count - 1, 1)
    )
    point = value[point_index]
    return point if isinstance(point, Mapping) else None


def _relative_at_ms(panel: Mapping[str, Any], value: Any) -> int | None:
    try:
        at_ms = int(value)
    except (TypeError, ValueError):
        return None
    try:
        start_ms = int(panel.get("start_ms"))
        end_ms = int(panel.get("end_ms"))
    except (TypeError, ValueError):
        return max(0, at_ms)
    if start_ms <= at_ms <= end_ms:
        return at_ms - start_ms
    return max(0, at_ms)


def _narrative_prompt(panels: Sequence[Mapping[str, Any]]) -> str:
    for panel in panels:
        value = panel.get("video_prompt") or panel.get("visual_prompt")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _panel_index(panel: Mapping[str, Any]) -> int:
    try:
        return max(1, int(panel.get("panel_index") or 1))
    except (TypeError, ValueError):
        return 1
