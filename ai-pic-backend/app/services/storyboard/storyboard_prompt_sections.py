"""Section builders for storyboard prompt v2 bundles."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

INLINE_CONSTRAINTS = (
    "No readable text, no subtitles, no speech bubbles, no UI, no watermark, "
    "no logo, no split-screen, no collage, no contact sheet, no frame labels."
)


def build_clip_identity(frame: Mapping[str, Any]) -> dict[str, Any]:
    shot_plan = _timeline_shot_plan(frame)
    return {
        "timeline_clip_id": frame.get("timeline_clip_id")
        or _source_value(frame, "clip_id")
        or shot_plan.get("clip_id"),
        "scene_id": frame.get("scene_id")
        or _source_value(frame, "scene_id")
        or shot_plan.get("scene_id"),
        "beat_id": frame.get("beat_id")
        or _source_value(frame, "beat_id")
        or shot_plan.get("beat_id"),
        "frame_number": frame.get("frame_number"),
        "start_ms": frame.get("start_ms"),
        "end_ms": frame.get("end_ms"),
    }


def prompt_layers(frame: Mapping[str, Any]) -> dict[str, Any]:
    layers: dict[str, Any] = {}
    keys = (
        "direction_anchor",
        "aesthetic_reference",
        "shot_type",
        "camera_movement",
        "composition_geometry",
        "motion_timeline",
        "emotional_landing",
        "prompt_method",
    )
    candidates = (
        frame.get("shot_plan_prompt_layers"),
        frame.get("timeline_shot_plan"),
        _timeline_shot_plan(frame),
    )
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            continue
        for key in keys:
            if key in layers:
                continue
            value = candidate.get(key)
            if key == "motion_timeline":
                motion = motion_points(value)
                if motion:
                    layers[key] = motion
            elif isinstance(value, str) and value.strip():
                layers[key] = value.strip()
    for key, value in {
        "shot_type": frame.get("shot_type"),
        "camera_movement": frame.get("camera_movement"),
        "composition_geometry": frame.get("composition"),
    }.items():
        if key not in layers and isinstance(value, str) and value.strip():
            layers[key] = value.strip()
    return layers


def build_image_prompt(
    frame: Mapping[str, Any],
    layers: Mapping[str, Any],
    *,
    subject: str,
    reference_notes: Sequence[Mapping[str, Any]],
) -> str:
    identity = build_clip_identity(frame)
    lines = [
        "Storyboard Prompt v2 - single cinematic movie still.",
        (
            "Clip identity: "
            f"clip={identity.get('timeline_clip_id') or 'unknown'}, "
            f"scene={identity.get('scene_id') or 'unknown'}, "
            f"beat={identity.get('beat_id') or 'unknown'}."
        ),
        f"Subject and action: {subject}",
        f"Direction anchor: {layers.get('direction_anchor') or subject}",
        f"Aesthetic reference: {layers.get('aesthetic_reference') or ''}",
        f"Shot type: {layers.get('shot_type') or frame.get('shot_type') or ''}",
        (
            "Camera movement intent: "
            f"{layers.get('camera_movement') or frame.get('camera_movement') or ''}"
        ),
        (
            "Composition geometry: "
            f"{layers.get('composition_geometry') or frame.get('composition') or ''}"
        ),
    ]
    motion = motion_text(layers.get("motion_timeline"))
    if motion:
        lines.append(f"Motion timeline as still-frame context: {motion}")
    landing = layers.get("emotional_landing")
    if landing:
        lines.append(f"Emotional landing: {landing}")
    refs = reference_notes_text(reference_notes)
    if refs:
        lines.append(f"Reference images: {refs}")
    lines.extend(
        [
            (
                "Frame contract: one frame only; no multi-panel layout; preserve "
                "character identity, costume, environment light, color temperature, "
                "spatial direction, and lens continuity."
            ),
            f"Constraints: {INLINE_CONSTRAINTS}",
        ]
    )
    return "\n".join(line for line in lines if line.strip())


def build_keyframe_prompt(
    image_prompt: str,
    layers: Mapping[str, Any],
    *,
    role: str,
) -> str:
    motion = motion_points(layers.get("motion_timeline"))
    point = motion[0] if role == "start" and motion else motion[-1] if motion else {}
    label = "Opening keyframe" if role == "start" else "Ending keyframe"
    action = point.get("action") if isinstance(point, Mapping) else None
    at_ms = point.get("at_ms") if isinstance(point, Mapping) else None
    lines = [
        image_prompt,
        f"{label}: emphasize the {'start' if role == 'start' else 'final'} state of the shot.",
    ]
    if action:
        lines.append(f"{label} motion beat: {at_ms}ms: {action}")
    lines.append(
        "Keep the same subject, wardrobe, environment, lens language, and lighting continuity."
    )
    return "\n".join(lines)


def build_i2v_motion_prompt(frame: Mapping[str, Any], layers: Mapping[str, Any]) -> str:
    lines = [
        "Use the reference image for identity, wardrobe, environment, composition, and lighting.",
        "Generate only the selected Timeline clip; do not reveal other storyboard panels.",
    ]
    camera = layers.get("camera_movement") or frame.get("camera_movement")
    if camera:
        lines.append(f"Camera movement: {camera}")
    motion = motion_text(layers.get("motion_timeline"))
    if motion:
        lines.append(f"Motion timeline: {motion}")
    landing = layers.get("emotional_landing")
    if landing:
        lines.append(f"Ending mood and rhythm: {landing}")
    if not motion:
        action = first_text(_shot_plan_value(frame, "action"), frame.get("beat_text"))
        if action:
            lines.append(f"Action: {action}")
    lines.append(
        "Avoid adding new characters, props, text, captions, UI, logos, or extra scene cuts."
    )
    return "\n".join(lines)


def motion_points(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    points: list[dict[str, Any]] = []
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


def motion_text(value: Any) -> str:
    return " / ".join(
        f"{point['at_ms']}ms: {point['action']}" for point in motion_points(value)
    )


def reference_note(note: Mapping[str, Any]) -> str:
    kind = note.get("type")
    name = note.get("name")
    if kind == "character":
        return f"character {name or 'unknown'} anchor"
    if kind == "environment":
        return "environment anchor"
    if kind == "frame":
        return "previous frame reference"
    if kind == "user":
        return "user supplied reference"
    return "reference image"


def reference_notes_text(notes: Sequence[Mapping[str, Any]]) -> str:
    values = [reference_note(note) for note in notes]
    return " | ".join(value for value in values if value)


def first_text(*values: Any) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _shot_plan_value(frame: Mapping[str, Any], key: str) -> Any:
    return _timeline_shot_plan(frame).get(key)


def _timeline_shot_plan(frame: Mapping[str, Any]) -> Mapping[str, Any]:
    plan = frame.get("timeline_shot_plan")
    if isinstance(plan, Mapping):
        return plan
    source_refs = frame.get("source_refs")
    if isinstance(source_refs, Mapping):
        plan = source_refs.get("timeline_shot_plan")
        if isinstance(plan, Mapping):
            return plan
    return {}


def _source_value(frame: Mapping[str, Any], key: str) -> Any:
    source = frame.get("source")
    if isinstance(source, Mapping):
        return source.get(key)
    return None
