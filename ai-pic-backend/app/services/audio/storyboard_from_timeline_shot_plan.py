from __future__ import annotations

from typing import Any
from uuid import uuid4

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


def build_storyboard_frames_from_timeline_shot_plan(
    *,
    timeline_spec: dict[str, Any],
) -> list[dict[str, Any]]:
    tracks = timeline_spec.get("tracks")
    if not isinstance(tracks, list):
        return []

    timeline_id = timeline_spec.get("timeline_id")
    timeline_version = timeline_spec.get("version")
    source_audio_version = timeline_spec.get("source_audio_timeline_version")
    frames: list[dict[str, Any]] = []
    scene_index_map: dict[Any, int] = {}
    next_scene_index = 1
    for clip in _clips_for_track(tracks, "video"):
        source_refs = (
            clip.get("source_refs") if isinstance(clip.get("source_refs"), dict) else {}
        )
        shot_plan = source_refs.get("timeline_shot_plan")
        if not isinstance(shot_plan, dict):
            continue
        start_ms = clip.get("start_ms")
        end_ms = clip.get("end_ms")
        duration_ms = clip.get("duration_ms")
        if start_ms is None or end_ms is None or duration_ms is None:
            continue
        scene_id = clip.get("scene_id")
        if scene_id is not None and scene_id not in scene_index_map:
            scene_index_map[scene_id] = next_scene_index
            next_scene_index += 1
        frames.append(
            _frame_from_shot_plan(
                clip=clip,
                shot_plan=shot_plan,
                frame_number=len(frames) + 1,
                scene_index=scene_index_map.get(scene_id),
                timeline_id=timeline_id,
                timeline_version=timeline_version,
                source_audio_version=source_audio_version,
            )
        )
    return frames


def _frame_from_shot_plan(
    *,
    clip: dict[str, Any],
    shot_plan: dict[str, Any],
    frame_number: int,
    scene_index: int | None,
    timeline_id: Any,
    timeline_version: Any,
    source_audio_version: Any,
) -> dict[str, Any]:
    description = str(
        shot_plan.get("plot") or clip.get("text") or shot_plan.get("action") or ""
    ).strip()
    prompt_layers = _shot_plan_prompt_layers(shot_plan)
    prompt_description = _prompt_description_from_shot_plan(
        shot_plan=shot_plan,
        description=description,
        prompt_layers=prompt_layers,
    )
    frame = {
        "frame_id": str(uuid4()),
        "frame_number": frame_number,
        "scene_id": clip.get("scene_id"),
        "scene_number": clip.get("scene_number"),
        "scene_index": scene_index,
        "description": description,
        "beat_type": clip.get("beat_type") or "shot_plan",
        "speaker_name": None,
        "beat_text": shot_plan.get("dialogue_source") or clip.get("text"),
        "characters": _shot_plan_characters(shot_plan),
        "prompt_description": prompt_description,
        "duration_seconds": round(int(clip["duration_ms"]) / 1000.0, 3),
        "generation_source": "timeline_spec",
        "generation_method": "timeline_shot_plan",
        "status": "draft",
        "start_ms": int(clip["start_ms"]),
        "end_ms": int(clip["end_ms"]),
        "timeline_clip_id": clip.get("clip_id"),
        "timeline_track_type": "video",
        "timeline_id": timeline_id,
        "timeline_version": timeline_version,
        "source_audio_timeline_version": source_audio_version,
        "source": _frame_source(clip, timeline_id, timeline_version),
        "timeline_shot_plan": shot_plan,
    }
    if prompt_layers:
        frame["shot_plan_prompt_layers"] = prompt_layers
    if shot_plan.get("shot_type"):
        frame["shot_type"] = str(shot_plan["shot_type"]).strip()
    if shot_plan.get("camera_movement"):
        frame["camera_movement"] = str(shot_plan["camera_movement"]).strip()
    elif shot_plan.get("camera"):
        frame["camera_movement"] = str(shot_plan["camera"]).strip()
    if shot_plan.get("composition_geometry"):
        frame["composition"] = str(shot_plan["composition_geometry"]).strip()
    if shot_plan.get("video_prompt"):
        frame["ai_prompt"] = str(shot_plan["video_prompt"]).strip()
    return frame


def _frame_source(
    clip: dict[str, Any],
    timeline_id: Any,
    timeline_version: Any,
) -> dict[str, Any]:
    return {
        "kind": "timeline_clip",
        "clip_id": clip.get("clip_id"),
        "track_type": "video",
        "scene_id": clip.get("scene_id"),
        "beat_id": clip.get("beat_id"),
        "timeline_id": timeline_id,
        "timeline_version": timeline_version,
        "shot_plan": "timeline_shot_plan",
    }


def _clips_for_track(tracks: list[Any], track_type: str) -> list[dict[str, Any]]:
    for track in tracks:
        if not isinstance(track, dict):
            continue
        if track.get("track_type") != track_type and track.get("type") != track_type:
            continue
        clips = track.get("clips")
        return [clip for clip in clips or [] if isinstance(clip, dict)]
    return []


def _shot_plan_characters(shot_plan: dict[str, Any]) -> list[str]:
    anchor = shot_plan.get("character_anchor")
    if not isinstance(anchor, str) or not anchor.strip():
        return []
    return [anchor.strip()]


def _shot_plan_prompt_layers(shot_plan: dict[str, Any]) -> dict[str, Any]:
    layers: dict[str, Any] = {}
    for key in PROMPT_LAYER_KEYS:
        value = shot_plan.get(key)
        if key == "motion_timeline":
            normalized_motion = _normalize_motion_timeline(value)
            if normalized_motion:
                layers[key] = normalized_motion
            continue
        if isinstance(value, str) and value.strip():
            layers[key] = value.strip()
    return layers


def _normalize_motion_timeline(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    points: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        action = item.get("action")
        if not isinstance(action, str) or not action.strip():
            continue
        at_ms = item.get("at_ms")
        try:
            at_ms_int = int(at_ms)
        except (TypeError, ValueError):
            continue
        points.append({"at_ms": at_ms_int, "action": action.strip()})
    return points


def _prompt_description_from_shot_plan(
    *,
    shot_plan: dict[str, Any],
    description: str,
    prompt_layers: dict[str, Any],
) -> str:
    fallback = str(
        shot_plan.get("visual_prompt") or shot_plan.get("video_prompt") or description
    ).strip()
    if not prompt_layers:
        return fallback

    lines = [
        f"Direction: {prompt_layers.get('direction_anchor') or fallback}",
        f"Aesthetic reference: {prompt_layers.get('aesthetic_reference') or shot_plan.get('style') or ''}",
        f"Shot: {prompt_layers.get('shot_type') or shot_plan.get('camera') or ''}",
        f"Camera: {prompt_layers.get('camera_movement') or shot_plan.get('camera') or ''}",
        f"Composition geometry: {prompt_layers.get('composition_geometry') or ''}",
    ]
    motion = _motion_timeline_text(prompt_layers.get("motion_timeline"))
    if motion:
        lines.append(f"Motion timeline: {motion}")
    landing = prompt_layers.get("emotional_landing")
    if landing:
        lines.append(f"Emotional landing: {landing}")
    if fallback:
        lines.append(f"Visual prompt: {fallback}")
    return "\n".join(line for line in lines if line.strip())


def _motion_timeline_text(value: Any) -> str:
    if not isinstance(value, list):
        return ""
    parts = []
    for item in value:
        if not isinstance(item, dict):
            continue
        at_ms = item.get("at_ms")
        action = item.get("action")
        if at_ms is None or not action:
            continue
        parts.append(f"{at_ms}ms: {action}")
    return " / ".join(parts)
