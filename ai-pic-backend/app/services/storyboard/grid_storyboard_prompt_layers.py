"""Prompt-layer helpers for Timeline-backed grid storyboards."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping

PROMPT_LAYER_KEYS = (
    "direction_anchor",
    "aesthetic_reference",
    "shot_type",
    "camera_movement",
    "composition_geometry",
    "motion_timeline",
    "emotional_landing",
    "prompt_method",
)


def shot_plan_prompt_layers(shot_plan: Mapping[str, Any]) -> Dict[str, Any]:
    layers: Dict[str, Any] = {}
    for key in PROMPT_LAYER_KEYS:
        value = shot_plan.get(key)
        if key == "motion_timeline":
            motion = normalize_motion_timeline(value)
            if motion:
                layers[key] = motion
            continue
        if isinstance(value, str) and value.strip():
            layers[key] = value.strip()
    return layers


def normalize_motion_timeline(value: Any) -> List[Dict[str, Any]]:
    if not isinstance(value, list):
        return []
    points: List[Dict[str, Any]] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        action = item.get("action")
        if not isinstance(action, str) or not action.strip():
            continue
        try:
            at_ms = int(item.get("at_ms"))
        except (TypeError, ValueError):
            continue
        points.append({"at_ms": at_ms, "action": action.strip()})
    return points


def motion_timeline_text(value: Any, *, separator: str = ": ") -> str:
    if not isinstance(value, list):
        return ""
    parts = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        at_ms = item.get("at_ms")
        action = item.get("action")
        if at_ms is None or not action:
            continue
        parts.append(f"{at_ms}ms{separator}{action}")
    return " / ".join(parts)


def build_panel_prompt(panel: Mapping[str, Any]) -> str:
    return (
        f"Panel {panel.get('panel_index')} "
        f"(row {panel.get('row')}, column {panel.get('column')}, "
        f"clip {panel.get('clip_id') or 'unknown'}): "
        f"{panel.get('visual_prompt') or ''}; "
        f"framing: {panel.get('shot_type') or ''}; "
        f"direction: {panel.get('direction_anchor') or ''}; "
        f"aesthetic: {panel.get('aesthetic_reference') or ''}; "
        f"composition: {panel.get('composition_geometry') or ''}; "
        f"motion: {motion_timeline_text(panel.get('motion_timeline'))}; "
        f"emotional landing: {panel.get('emotional_landing') or ''}"
    )
