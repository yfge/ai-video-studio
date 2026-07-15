"""Prompt rendering helpers for grid and clip storyboard sheets."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from app.services.storyboard.grid_storyboard_layout import grid_layout
from app.services.storyboard.grid_storyboard_prompt_context import (
    bound_context_lines,
    panel_context_text,
    panel_motion_prompt,
)
from app.services.storyboard.grid_storyboard_prompt_layers import motion_timeline_text


def build_grid_storyboard_sheet_prompt(
    panels: Sequence[Mapping[str, Any]],
    *,
    style: str | None = None,
) -> str:
    """Compose a prompt for one generated storyboard sheet image."""

    if not panels:
        raise ValueError("grid_storyboard_panels_required")

    layout = grid_layout(len(panels))
    lines = [
        (
            f"Create a {layout.panel_count}-panel {layout.label} storyboard sheet "
            "for a vertical short-drama sequence."
        ),
        "Arrange panels left-to-right, top-to-bottom with clean gutters and stable character continuity.",
    ]
    if style:
        lines.append(f"Visual style: {style}.")
    lines.extend(_sheet_constraints())
    for panel in panels:
        panel_index = panel.get("panel_index")
        clip_id = panel.get("clip_id") or "unknown"
        visual_prompt = panel.get("visual_prompt") or ""
        lines.append(
            (
                f"- Panel {panel_index} / clip {clip_id}: {visual_prompt}; "
                f"direction: {panel.get('direction_anchor') or ''}; "
                f"aesthetic: {panel.get('aesthetic_reference') or ''}; "
                f"composition: {panel.get('composition_geometry') or ''}; "
                f"motion: {motion_timeline_text(panel.get('motion_timeline'), separator=' ')}; "
                f"emotional landing: {panel.get('emotional_landing') or ''}"
            ).strip()
        )

    return "\n".join(lines)


def build_clip_storyboard_sheet_prompt(
    panels: Sequence[Mapping[str, Any]],
    *,
    style: str | None = None,
) -> str:
    """Compose a storyboard sheet prompt for one selected clip."""

    if not panels:
        raise ValueError("clip_storyboard_panels_required")

    layout = grid_layout(len(panels))
    clip_id = panels[0].get("clip_id") or "unknown"
    lines = [
        (
            f"Create a {layout.panel_count}-panel {layout.label} storyboard sheet "
            f"for one selected Timeline clip: {clip_id}."
        ),
        "Each panel is a key visual moment inside the same shot, not a different episode or Timeline clip.",
        "Arrange panels left-to-right, top-to-bottom with clean gutters and stable character continuity.",
        (
            "Keep every visible character's face, hairstyle, wardrobe, body proportions, "
            "age, and gender identical across panels; only pose, expression, framing, and action may change."
        ),
        (
            "Make every panel visibly distinct at thumbnail size: use its specified action beat, "
            "camera distance, angle, and composition; do not repeat near-identical poses or framing."
        ),
    ]
    lines.extend(_style_contract(style))
    lines.extend(bound_context_lines(panels[0]))
    lines.extend(_sheet_constraints())
    for panel in panels:
        lines.append(
            (
                f"- Panel {panel.get('panel_index')} / clip {clip_id}: "
                f"{panel.get('visual_prompt') or ''}; "
                f"framing: {panel.get('shot_type') or ''}; "
                f"direction: {panel.get('direction_anchor') or ''}; "
                f"{_aesthetic_clause(panel.get('aesthetic_reference'), style)}"
                f"composition: {panel.get('composition_geometry') or ''}; "
                f"panel action anchor: {_panel_action_anchor_text(panel)}; "
                f"emotional landing: {panel.get('emotional_landing') or ''}; "
                f"{panel_context_text(panel)}"
            ).strip()
        )
    return "\n".join(lines)


def _panel_action_anchor_text(panel: Mapping[str, Any]) -> str:
    motion_timeline = panel.get("motion_timeline")
    if not isinstance(motion_timeline, list) or not motion_timeline:
        return ""
    try:
        panel_index = max(1, int(panel.get("panel_index") or 1))
    except (TypeError, ValueError):
        panel_index = 1
    point = motion_timeline[min(panel_index - 1, len(motion_timeline) - 1)]
    return motion_timeline_text([point], separator=" ")


def build_grid_storyboard_video_prompt(panel: Mapping[str, Any]) -> str:
    """Compose the per-clip image-to-video prompt for one grid panel."""

    panel_index = panel.get("panel_index")
    clip_id = panel.get("clip_id") or "unknown"
    return "\n".join(
        [
            f"Use panel {panel_index} only from the storyboard sheet as the visual reference for clip {clip_id}.",
            "Generate only this shot; do not animate or reveal other panels from the sheet.",
            panel_motion_prompt(panel),
        ]
    )


def build_clip_storyboard_video_prompt(panel: Mapping[str, Any]) -> str:
    """Compose the per-clip image-to-video prompt from one clip storyboard panel."""

    panel_index = panel.get("panel_index")
    clip_id = panel.get("clip_id") or "unknown"
    return "\n".join(
        [
            f"Use panel {panel_index} only from the clip storyboard sheet as the visual reference for clip {clip_id}.",
            "Generate only this selected Timeline clip; do not animate other panels or imply a full-episode storyboard.",
            panel_motion_prompt(panel),
        ]
    )


def _sheet_constraints() -> list[str]:
    return [
        "Small panel numbers are allowed only in the panel borders.",
        "No subtitles, speech bubbles, captions, readable UI text, watermarks, or title cards inside panels.",
        "Panel briefs:",
    ]


def _style_contract(style: str | None) -> list[str]:
    normalized = str(style or "").strip().lower()
    if normalized == "live_action":
        return [
            (
                "Authoritative visual style: photorealistic live action with real human "
                "faces, natural skin texture, practical lighting, and cinematic photography."
            ),
            (
                "Ignore any conflicting non-live-action style language in inherited panel briefs."
            ),
        ]
    if normalized == "3d_cartoon":
        return [
            (
                "Authoritative visual style: unmistakably non-photorealistic "
                "stylized 3D feature animation."
            ),
            (
                "Use simplified sculpted face geometry, slightly exaggerated eyes "
                "and proportions, clean stylized hair clumps, and matte painted "
                "character shaders."
            ),
            (
                "Any reference photos define identity only: do not copy skin pores, "
                "photographic skin texture, lens bokeh, live-action lighting, or "
                "real-human portrait rendering."
            ),
            (
                "Every panel must look clearly like an animated film frame and must "
                "never be mistaken for a photograph."
            ),
            "Ignore conflicting photorealistic, live-action, or 2D illustration language in inherited panel briefs.",
        ]
    if normalized == "2d_cartoon":
        return [
            "Authoritative visual style: cohesive 2D animated illustration.",
            "Ignore conflicting photorealistic, live-action, or 3D-render language in inherited panel briefs.",
        ]
    return [f"Authoritative visual style: {style}."] if style else []


def _aesthetic_clause(value: Any, style: str | None) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    normalized_style = str(style or "").strip().lower()
    lowered = text.lower()
    conflicts: tuple[str, ...] = ()
    if normalized_style == "live_action":
        conflicts = ("pixar", "cartoon", "animation", "animated", "2d", "3d")
    elif normalized_style == "3d_cartoon":
        conflicts = ("photoreal", "live action", "live-action", "2d")
    elif normalized_style == "2d_cartoon":
        conflicts = ("photoreal", "live action", "live-action", "3d")
    if any(term in lowered for term in conflicts):
        return ""
    return f"aesthetic: {text}; "
