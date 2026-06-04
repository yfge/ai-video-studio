"""Bridge Timeline clip prompts into grid-storyboard prompt inputs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence

from app.services.storyboard.grid_storyboard_prompt_layers import (
    build_panel_prompt,
    motion_timeline_text,
    shot_plan_prompt_layers,
)

SUPPORTED_PANEL_COUNTS = (2, 4, 6, 9)


@dataclass(frozen=True)
class GridLayout:
    panel_count: int
    columns: int
    rows: int

    @property
    def label(self) -> str:
        return f"{self.columns}x{self.rows}"


def grid_layout(panel_count: int) -> GridLayout:
    """Return the smallest supported storyboard grid layout for a clip count."""

    requested_count = max(1, panel_count)
    normalized_count = next(
        (count for count in SUPPORTED_PANEL_COUNTS if requested_count <= count),
        SUPPORTED_PANEL_COUNTS[-1],
    )

    if normalized_count == 2:
        return GridLayout(panel_count=2, columns=2, rows=1)
    if normalized_count == 4:
        return GridLayout(panel_count=4, columns=2, rows=2)
    if normalized_count == 6:
        return GridLayout(panel_count=6, columns=3, rows=2)
    return GridLayout(panel_count=9, columns=3, rows=3)


def build_grid_storyboard_panels(
    timeline_spec: Mapping[str, Any],
    panel_count: int,
) -> List[Dict[str, Any]]:
    """Build ordered grid panels from Timeline video clips.

    Timeline remains the source of truth. A timeline_shot_plan prompt bundle wins
    when available, with clip text fields used as a compatibility fallback.
    """

    layout = grid_layout(panel_count)
    clips = _timeline_video_clips(timeline_spec)[: layout.panel_count]
    panels: List[Dict[str, Any]] = []

    for index, clip in enumerate(clips, start=1):
        clip_id = clip.get("clip_id") or clip.get("id")
        shot_plan = _timeline_shot_plan(clip)
        visual_prompt = _first_text(
            shot_plan.get("visual_prompt"),
            shot_plan.get("image_prompt"),
            clip.get("ai_prompt"),
            clip.get("prompt"),
            clip.get("text"),
            clip.get("label"),
            clip.get("description"),
        )
        video_prompt = _first_text(
            shot_plan.get("video_prompt"),
            clip.get("video_prompt"),
            visual_prompt,
        )
        prompt_layers = shot_plan_prompt_layers(shot_plan)
        row = ((index - 1) // layout.columns) + 1
        column = ((index - 1) % layout.columns) + 1
        panel = {
            "panel_id": f"grid_panel_{index:03d}",
            "panel_index": index,
            "row": row,
            "column": column,
            "clip_id": clip_id,
            "scene_id": clip.get("scene_id"),
            "beat_id": clip.get("beat_id"),
            "start_ms": clip.get("start_ms"),
            "end_ms": clip.get("end_ms"),
            "duration_ms": _duration_ms(clip),
            "visual_prompt": visual_prompt,
            "video_prompt": video_prompt,
            "source_refs": clip.get("source_refs") or {},
        }
        panel.update(prompt_layers)
        panel["storyboard_panel_prompt"] = build_panel_prompt(panel)
        panels.append(panel)

    return panels


def build_clip_storyboard_panels(
    clip: Mapping[str, Any],
    panel_count: int,
) -> List[Dict[str, Any]]:
    """Build storyboard panels for one selected Timeline video clip."""

    layout = grid_layout(panel_count)
    clip_id = clip.get("clip_id") or clip.get("id")
    shot_plan = _timeline_shot_plan(clip)
    visual_prompt = _first_text(
        shot_plan.get("visual_prompt"),
        shot_plan.get("image_prompt"),
        clip.get("ai_prompt"),
        clip.get("prompt"),
        clip.get("text"),
        clip.get("label"),
        clip.get("description"),
    )
    video_prompt = _first_text(
        shot_plan.get("video_prompt"),
        clip.get("video_prompt"),
        visual_prompt,
    )
    prompt_layers = shot_plan_prompt_layers(shot_plan)
    motion = prompt_layers.get("motion_timeline")
    panels: List[Dict[str, Any]] = []
    for index in range(1, layout.panel_count + 1):
        row = ((index - 1) // layout.columns) + 1
        column = ((index - 1) % layout.columns) + 1
        panel = {
            "panel_id": f"clip_storyboard_panel_{index:03d}",
            "panel_index": index,
            "row": row,
            "column": column,
            "clip_id": clip_id,
            "scene_id": clip.get("scene_id"),
            "beat_id": clip.get("beat_id"),
            "start_ms": clip.get("start_ms"),
            "end_ms": clip.get("end_ms"),
            "duration_ms": _duration_ms(clip),
            "visual_prompt": _panel_visual_prompt(visual_prompt, motion, index),
            "video_prompt": video_prompt,
            "source_refs": clip.get("source_refs") or {},
        }
        panel.update(prompt_layers)
        panel["storyboard_panel_prompt"] = build_panel_prompt(panel)
        panels.append(panel)
    return panels


def build_grid_storyboard_sheet_prompt(
    panels: Sequence[Mapping[str, Any]],
    *,
    style: Optional[str] = None,
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
    lines.extend(
        [
            "Small panel numbers are allowed only in the panel borders.",
            "No subtitles, speech bubbles, captions, readable UI text, watermarks, or title cards inside panels.",
            "Panel briefs:",
        ]
    )
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
    style: Optional[str] = None,
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
    ]
    if style:
        lines.append(f"Visual style: {style}.")
    lines.extend(
        [
            "Small panel numbers are allowed only in the panel borders.",
            "No subtitles, speech bubbles, captions, readable UI text, watermarks, or title cards inside panels.",
            "Panel briefs:",
        ]
    )
    for panel in panels:
        lines.append(
            (
                f"- Panel {panel.get('panel_index')} / clip {clip_id}: "
                f"{panel.get('visual_prompt') or ''}; "
                f"direction: {panel.get('direction_anchor') or ''}; "
                f"aesthetic: {panel.get('aesthetic_reference') or ''}; "
                f"composition: {panel.get('composition_geometry') or ''}; "
                f"motion: {motion_timeline_text(panel.get('motion_timeline'), separator=' ')}; "
                f"emotional landing: {panel.get('emotional_landing') or ''}"
            ).strip()
        )
    return "\n".join(lines)


def build_grid_storyboard_video_prompt(panel: Mapping[str, Any]) -> str:
    """Compose the per-clip image-to-video prompt for one grid panel."""

    panel_index = panel.get("panel_index")
    clip_id = panel.get("clip_id") or "unknown"
    video_prompt = panel.get("video_prompt") or panel.get("visual_prompt") or ""
    return "\n".join(
        [
            f"Use panel {panel_index} only from the storyboard sheet as the visual reference for clip {clip_id}.",
            "Generate only this shot; do not animate or reveal other panels from the sheet.",
            "Preserve the character, costume, environment, composition, and lighting shown in the selected panel.",
            f"Direction anchor: {panel.get('direction_anchor') or ''}",
            f"Aesthetic reference: {panel.get('aesthetic_reference') or ''}",
            f"Composition geometry: {panel.get('composition_geometry') or ''}",
            f"Motion timeline: {motion_timeline_text(panel.get('motion_timeline'))}",
            f"Emotional landing: {panel.get('emotional_landing') or ''}",
            str(video_prompt),
        ]
    )


def build_clip_storyboard_video_prompt(panel: Mapping[str, Any]) -> str:
    """Compose the per-clip image-to-video prompt from one clip storyboard panel."""

    panel_index = panel.get("panel_index")
    clip_id = panel.get("clip_id") or "unknown"
    video_prompt = panel.get("video_prompt") or panel.get("visual_prompt") or ""
    return "\n".join(
        [
            f"Use panel {panel_index} only from the clip storyboard sheet as the visual reference for clip {clip_id}.",
            "Generate only this selected Timeline clip; do not animate other panels or imply a full-episode storyboard.",
            "Preserve the character, costume, environment, composition, and lighting shown in the selected panel.",
            f"Direction anchor: {panel.get('direction_anchor') or ''}",
            f"Aesthetic reference: {panel.get('aesthetic_reference') or ''}",
            f"Composition geometry: {panel.get('composition_geometry') or ''}",
            f"Motion timeline: {motion_timeline_text(panel.get('motion_timeline'))}",
            f"Emotional landing: {panel.get('emotional_landing') or ''}",
            str(video_prompt),
        ]
    )


def _timeline_video_clips(timeline_spec: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    tracks = timeline_spec.get("tracks")
    if not isinstance(tracks, list):
        return []

    clips: List[Mapping[str, Any]] = []
    for track in tracks:
        if not isinstance(track, Mapping):
            continue
        track_type = track.get("track_type") or track.get("type") or track.get("kind")
        if track_type != "video":
            continue
        track_clips = track.get("clips")
        if not isinstance(track_clips, list):
            continue
        clips.extend(clip for clip in track_clips if isinstance(clip, Mapping))

    return sorted(clips, key=lambda clip: clip.get("start_ms") or 0)


def _timeline_shot_plan(clip: Mapping[str, Any]) -> Mapping[str, Any]:
    source_refs = clip.get("source_refs")
    if not isinstance(source_refs, Mapping):
        return {}
    shot_plan = source_refs.get("timeline_shot_plan")
    return shot_plan if isinstance(shot_plan, Mapping) else {}


def _panel_visual_prompt(
    visual_prompt: str,
    motion_timeline: Any,
    panel_index: int,
) -> str:
    if isinstance(motion_timeline, list) and motion_timeline:
        point = motion_timeline[min(panel_index - 1, len(motion_timeline) - 1)]
        if isinstance(point, Mapping):
            action = point.get("action")
            at_ms = point.get("at_ms")
            if isinstance(action, str) and action.strip():
                return (
                    f"{visual_prompt} Key moment {panel_index}"
                    f" at {at_ms}ms: {action.strip()}"
                ).strip()
    return f"{visual_prompt} Key moment {panel_index}".strip()


def _first_text(*values: Any) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _duration_ms(clip: Mapping[str, Any]) -> Optional[int]:
    start_ms = clip.get("start_ms")
    end_ms = clip.get("end_ms")
    if isinstance(start_ms, (int, float)) and isinstance(end_ms, (int, float)):
        return max(0, int(end_ms - start_ms))
    return None
