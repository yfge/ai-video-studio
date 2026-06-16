"""Prompt helpers for selected Timeline clip visual generation."""

from __future__ import annotations

from typing import Any, Mapping

from app.services.storyboard.grid_storyboard_prompt_layers import (
    motion_timeline_text,
    normalize_motion_timeline,
)

PROMPT_CONTRACT_VERSION = "timeline_clip_visual_prompt_v1"
INLINE_CONSTRAINTS = (
    "No subtitles, no speech bubbles, no readable UI text, no watermarks, "
    "no logos, no split-screen, no collage, no storyboard gutters."
)
_CLIP_PROMPT_KEYS = ("ai_prompt", "prompt", "description", "text", "label")


def build_timeline_clip_keyframe_frames(
    clip: Mapping[str, Any],
    override: str | None = None,
) -> tuple[list[dict[str, str]], dict[str, str]]:
    context = _prompt_context(clip, override)
    if not _has_prompt_content(context):
        return [], _metadata(context)
    return [
        {"role": "start_frame", "prompt": _keyframe_prompt(context, "start_frame")},
        {"role": "end_frame", "prompt": _keyframe_prompt(context, "end_frame")},
    ], _metadata(context)


def build_timeline_clip_video_motion_prompt(
    clip: Mapping[str, Any],
    override: str | None = None,
) -> tuple[str, dict[str, str]]:
    context = _prompt_context(clip, override)
    if not _has_prompt_content(context):
        return "", _metadata(context)
    if context["motion_prompt_source"] == "operator_override":
        return context["motion_prompt"], _metadata(context)
    return _video_motion_prompt(context), _metadata(context)


def _prompt_context(clip: Mapping[str, Any], override: str | None) -> dict[str, Any]:
    shot_plan = _timeline_shot_plan(clip)
    visual_prompt, visual_source = _first_text_with_source(
        ("timeline_shot_plan.visual_prompt", shot_plan.get("visual_prompt")),
        ("timeline_shot_plan.image_prompt", shot_plan.get("image_prompt")),
        *((f"clip.{key}", clip.get(key)) for key in _CLIP_PROMPT_KEYS),
    )
    override_text = _clean(override)
    if override_text:
        motion_prompt = override_text
        motion_source = "operator_override"
    else:
        motion_prompt, motion_source = _first_text_with_source(
            ("timeline_shot_plan.video_prompt", shot_plan.get("video_prompt")),
            ("timeline_shot_plan.visual_prompt", shot_plan.get("visual_prompt")),
            *(
                (f"clip.{key}", clip.get(key))
                for key in ("video_prompt", *_CLIP_PROMPT_KEYS)
            ),
        )
    return {
        "clip_id": _clean(clip.get("clip_id") or clip.get("id")) or "unknown",
        "visual_prompt": visual_prompt,
        "visual_prompt_source": visual_source,
        "motion_prompt": motion_prompt,
        "motion_prompt_source": motion_source,
        "direction_anchor": _clean(shot_plan.get("direction_anchor")),
        "aesthetic_reference": _clean(shot_plan.get("aesthetic_reference")),
        "shot_type": _clean(shot_plan.get("shot_type") or clip.get("shot_type")),
        "camera_movement": _clean(
            shot_plan.get("camera_movement") or clip.get("camera_movement")
        ),
        "composition_geometry": _clean(
            shot_plan.get("composition_geometry") or clip.get("composition")
        ),
        "motion_timeline": normalize_motion_timeline(shot_plan.get("motion_timeline")),
        "emotional_landing": _clean(shot_plan.get("emotional_landing")),
    }


def _keyframe_prompt(context: Mapping[str, Any], role: str) -> str:
    points = context.get("motion_timeline") or []
    point = points[0] if role == "start_frame" and points else points[-1] if points else {}
    label = "Opening keyframe" if role == "start_frame" else "Ending keyframe"
    state = "start state" if role == "start_frame" else "final state"
    lines = [
        f"{label} for selected Timeline clip {context['clip_id']}.",
        f"Show the {state} of the same shot, not a new scene.",
        f"Subject and visual plan: {context['visual_prompt']}",
        f"Motion intent: {context['motion_prompt']}",
    ]
    if point:
        lines.append(f"{label} motion beat: {point['at_ms']}ms: {point['action']}")
    for key, label_text in (
        ("direction_anchor", "Direction anchor"),
        ("aesthetic_reference", "Aesthetic reference"),
        ("shot_type", "Shot type"),
        ("camera_movement", "Camera movement"),
        ("composition_geometry", "Composition"),
        ("emotional_landing", "Emotional landing"),
    ):
        value = context.get(key)
        if value:
            lines.append(f"{label_text}: {value}")
    lines.append(
        "Preserve subject identity, wardrobe, environment, lens language, lighting, "
        "color temperature, and spatial direction."
    )
    lines.append(INLINE_CONSTRAINTS)
    return "\n".join(lines)


def _video_motion_prompt(context: Mapping[str, Any]) -> str:
    lines = [
        f"Generate only the selected Timeline clip {context['clip_id']}.",
        (
            "Use reference images for identity, wardrobe, environment, composition, "
            "and lighting continuity."
        ),
        f"Motion intent: {context['motion_prompt']}",
    ]
    if context.get("camera_movement"):
        lines.append(f"Camera movement: {context['camera_movement']}")
    motion = motion_timeline_text(context.get("motion_timeline") or [], separator=": ")
    if motion:
        lines.append(f"Motion timeline: {motion}")
    if context.get("emotional_landing"):
        lines.append(f"Ending rhythm and mood: {context['emotional_landing']}")
    lines.append(
        "Avoid adding new characters, extra cuts, storyboard gutters, or unrelated panels."
    )
    lines.append(INLINE_CONSTRAINTS)
    return "\n".join(lines)


def _metadata(context: Mapping[str, Any]) -> dict[str, str]:
    return {
        "prompt_contract_version": PROMPT_CONTRACT_VERSION,
        "visual_prompt_source": str(context["visual_prompt_source"]),
        "motion_prompt_source": str(context["motion_prompt_source"]),
    }


def _timeline_shot_plan(clip: Mapping[str, Any]) -> Mapping[str, Any]:
    source_refs = clip.get("source_refs")
    if isinstance(source_refs, Mapping):
        shot_plan = source_refs.get("timeline_shot_plan")
        if isinstance(shot_plan, Mapping):
            return shot_plan
    return {}


def _first_text_with_source(*values: tuple[str, Any]) -> tuple[str, str]:
    for source, value in values:
        text = _clean(value)
        if text:
            return text, source
    return "", "empty"


def _clean(value: Any) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else ""


def _has_prompt_content(context: Mapping[str, Any]) -> bool:
    return bool(
        context.get("visual_prompt")
        or context.get("motion_prompt")
        or context.get("motion_timeline")
    )
