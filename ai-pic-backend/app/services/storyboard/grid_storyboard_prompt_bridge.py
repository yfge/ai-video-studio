"""Bridge Timeline clip prompts into grid-storyboard prompt inputs."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional

from app.services.storyboard.clip_storyboard_panel_moments import (
    clip_panel_fallback_layers,
)
from app.services.storyboard.grid_storyboard_layout import grid_layout
from app.services.storyboard.grid_storyboard_prompt_layers import (
    build_panel_prompt,
    shot_plan_prompt_layers,
)
from app.services.storyboard.grid_storyboard_prompt_rendering import (
    build_clip_storyboard_sheet_prompt,
    build_clip_storyboard_video_prompt,
    build_grid_storyboard_sheet_prompt,
    build_grid_storyboard_video_prompt,
)

__all__ = [
    "build_clip_storyboard_panels",
    "build_clip_storyboard_sheet_prompt",
    "build_clip_storyboard_video_prompt",
    "build_grid_storyboard_panels",
    "build_grid_storyboard_sheet_prompt",
    "build_grid_storyboard_video_prompt",
    "grid_layout",
]


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
        fallback_layers = clip_panel_fallback_layers(
            clip,
            panel_index=index,
            panel_count=layout.panel_count,
        )
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
            "visual_prompt": _panel_visual_prompt(
                visual_prompt,
                motion,
                index,
                layout.panel_count,
                fallback_layers["panel_moment"],
            ),
            "video_prompt": video_prompt,
            "source_refs": clip.get("source_refs") or {},
        }
        panel.update(prompt_layers)
        panel["panel_moment"] = fallback_layers["panel_moment"]
        panel["shot_type"] = fallback_layers["shot_type"]
        panel["composition_geometry"] = _clip_panel_composition(
            fallback_layers["composition_geometry"],
            prompt_layers.get("composition_geometry"),
        )
        if not panel.get("motion_timeline"):
            panel["motion_timeline"] = fallback_layers["motion_timeline"]
        if not panel.get("camera_movement"):
            panel["camera_movement"] = fallback_layers["camera_movement"]
        if not panel.get("emotional_landing"):
            panel["emotional_landing"] = fallback_layers["emotional_landing"]
        panel["storyboard_panel_prompt"] = build_panel_prompt(panel)
        panels.append(panel)
    return panels


def _clip_panel_composition(panel_composition: Any, base_composition: Any) -> str:
    panel_text = str(panel_composition or "").strip()
    base_text = str(base_composition or "").strip()
    if panel_text and base_text:
        return (
            f"{panel_text}; preserve the clip's established screen direction and "
            f"blocking: {base_text}"
        )
    return panel_text or base_text


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
    panel_count: int,
    fallback_moment: str,
) -> str:
    if isinstance(motion_timeline, list) and motion_timeline:
        point_index = round(
            (panel_index - 1) * (len(motion_timeline) - 1) / max(panel_count - 1, 1)
        )
        point = motion_timeline[point_index]
        if isinstance(point, Mapping):
            action = point.get("action")
            at_ms = point.get("at_ms")
            if isinstance(action, str) and action.strip():
                return (
                    f"{visual_prompt} Moment {panel_index}"
                    f" at {at_ms}ms: {action.strip()}"
                ).strip()
    return f"{visual_prompt} {fallback_moment}".strip()


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
