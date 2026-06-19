from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any

from app.services.timeline_shot_plan_coercion import coerce_timeline_shot_plan_payload
from app.services.timeline_shot_plan_models import TimelineShotPlan
from app.services.timeline_shot_plan_styles import style_prompt_instruction

SHOT_PLAN_SCHEMA = TimelineShotPlan.model_json_schema()


def build_timeline_shot_plan_prompt(
    spec: dict[str, Any],
    *,
    style: str,
    clip_ids: set[str] | None = None,
) -> str:
    clips = _timeline_prompt_clips(spec, clip_ids=clip_ids)
    return (
        "Return only valid JSON. Generate a Timeline-native shot plan for every "
        "video clip below. Do not change clip_id, timing, or duration_ms. Use only "
        "the provided Timeline fields as story source. The output schema is: "
        '{"shots":[{"clip_id":str,"duration_ms":int,"plot":str,'
        '"dialogue_source":str,"visual_prompt":str,"video_prompt":str,'
        '"character_anchor":str,"camera":str,"action":str,'
        '"direction_anchor":str,"aesthetic_reference":str,"shot_type":str,'
        '"camera_movement":str,"composition_geometry":str,'
        '"motion_timeline":[{"at_ms":int,"action":str}],'
        '"emotional_landing":str,"prompt_method":str}]}. '
        f"Style must be {style}. {style_prompt_instruction(style)} "
        "Use the five-layer prompting method for every shot: "
        "1) direction_anchor gives the AI a direction, not a locked template; "
        "2) aesthetic_reference uses objective references such as camera/lens, "
        "film stock, named visual style, color pairing, or production design; "
        "3) composition_geometry describes screen positions, left/right/center, "
        "foreground/background, and geometric relationships; "
        "4) motion_timeline has 2-4 ordered action beats inside the clip duration, "
        "or 1 beat for very short silent pause clips; "
        "5) emotional_landing states the shot's final mood, rhythm, and light temperature. "
        "Set prompt_method to direction_reference_geometry_timeline_emotion_v1. "
        "Use the same protagonist anchor across all shots when character_anchor_hint is present. "
        "character_anchor must be a reusable visual descriptor, not only "
        "a bare character name. Supporting characters may appear only as secondary "
        "props/figures and must not replace the protagonist. "
        "Each video_prompt must include plot, dialogue_source, character_anchor, camera, action, "
        "style, duration, composition_geometry, motion_timeline, and emotional_landing. "
        "For silent pause/placeholder clips, do not invent dialogue; set dialogue_source "
        "to an empty string and describe only the visual pause/action. Timeline clips: "
        f"{clips}"
    )


def validate_timeline_shot_plan_matches(
    plan: dict[str, Any], spec: dict[str, Any]
) -> dict[str, Any] | None:
    video_by_id = {
        str(clip.get("clip_id")): clip for clip in clips_for_track(spec, "video")
    }
    shot_by_id = {str(shot.get("clip_id")): shot for shot in plan.get("shots") or []}
    missing = sorted(set(video_by_id) - set(shot_by_id))
    extra = sorted(set(shot_by_id) - set(video_by_id))
    if missing or extra:
        return {
            "message": "timeline shot plan clip mismatch",
            "missing": missing,
            "extra": extra,
        }
    for clip_id, shot in shot_by_id.items():
        clip = video_by_id[clip_id]
        expected = int(clip.get("duration_ms") or 0)
        if int(shot.get("duration_ms") or 0) != expected:
            return {
                "message": "timeline shot plan duration mismatch",
                "clip_id": clip_id,
                "expected_duration_ms": expected,
                "actual_duration_ms": shot.get("duration_ms"),
            }
        source_text = _strip_text(clip.get("text"))
        dialogue_text = _dialogue_text_for_video_clip(clip, spec)
        if source_text and not _strip_text(shot.get("plot")):
            return {
                "message": "timeline shot plan plot missing",
                "clip_id": clip_id,
            }
        if dialogue_text and not _strip_text(shot.get("dialogue_source")):
            return {
                "message": "timeline shot plan dialogue source missing",
                "clip_id": clip_id,
            }
        beat_type = str(clip.get("beat_type") or "").lower()
        if (
            beat_type not in {"pause", "placeholder"}
            and len(shot.get("motion_timeline") or []) < 2
        ):
            return {
                "message": "timeline shot plan motion timeline too short",
                "clip_id": clip_id,
            }
    return None


def apply_timeline_shot_plan(
    spec: dict[str, Any],
    plan: dict[str, Any],
    *,
    provider: str | None,
    model: str | None,
    style: str,
) -> dict[str, Any]:
    updated = deepcopy(spec)
    generated_at = datetime.utcnow().isoformat() + "Z"
    shot_by_id = {str(shot["clip_id"]): shot for shot in plan["shots"]}
    for clip in clips_for_track(updated, "video"):
        clip_id = str(clip.get("clip_id"))
        refs = clip.setdefault("source_refs", {})
        if not isinstance(refs, dict):
            refs = {}
            clip["source_refs"] = refs
        refs["timeline_shot_plan"] = {
            **shot_by_id[clip_id],
            "style": style,
            "provider": provider,
            "model": model,
            "generated_at": generated_at,
            "source": "timeline_spec",
        }
        refs["provider_chain_stage"] = "timeline_shot_plan_generated"

    source = updated.setdefault("source", {})
    if isinstance(source, dict):
        source["timeline_shot_plan"] = {
            "style": style,
            "provider": provider,
            "model": model,
            "generated_at": generated_at,
            "clip_count": len(plan["shots"]),
        }
    return updated


def clips_for_track(spec: dict[str, Any], track_type: str) -> list[dict[str, Any]]:
    tracks = spec.get("tracks")
    if not isinstance(tracks, list):
        return []
    for track in tracks:
        if not isinstance(track, dict):
            continue
        if track.get("track_type") == track_type or track.get("type") == track_type:
            clips = track.get("clips")
            return [clip for clip in clips or [] if isinstance(clip, dict)]
    return []


def _timeline_prompt_clips(
    spec: dict[str, Any],
    *,
    clip_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    dialogue_by_key = _clips_by_scene_beat(spec, "dialogue")
    subtitle_by_key = _clips_by_scene_beat(spec, "subtitle")
    prompt_clips: list[dict[str, Any]] = []
    for clip in clips_for_track(spec, "video"):
        if clip_ids is not None and str(clip.get("clip_id")) not in clip_ids:
            continue
        key = _scene_beat_key(clip)
        dialogue_clip = dialogue_by_key.get(key) or {}
        subtitle_clip = subtitle_by_key.get(key) or {}
        source_refs = clip.get("source_refs") or {}
        source_refs = source_refs if isinstance(source_refs, dict) else {}
        prompt_clips.append(
            {
                "clip_id": clip.get("clip_id"),
                "scene_id": clip.get("scene_id"),
                "beat_id": clip.get("beat_id"),
                "ordinal": clip.get("ordinal"),
                "start_ms": clip.get("start_ms"),
                "end_ms": clip.get("end_ms"),
                "duration_ms": clip.get("duration_ms"),
                "plot": clip.get("text") or dialogue_clip.get("text") or "",
                "dialogue": dialogue_clip.get("text")
                or subtitle_clip.get("text")
                or "",
                "speaker_name": dialogue_clip.get("speaker_name"),
                "dialogue_action": dialogue_clip.get("dialogue_action"),
                "dialogue_emotion": dialogue_clip.get("dialogue_emotion"),
                "character_name": source_refs.get("character_name"),
                "character_appearance_prompt": source_refs.get(
                    "character_appearance_prompt"
                ),
                "character_anchor_hint": source_refs.get("character_anchor_hint"),
            }
        )
    return prompt_clips


def _clips_by_scene_beat(
    spec: dict[str, Any],
    track_type: str,
) -> dict[tuple[Any, Any, Any], dict[str, Any]]:
    return {_scene_beat_key(clip): clip for clip in clips_for_track(spec, track_type)}


def _scene_beat_key(clip: dict[str, Any]) -> tuple[Any, Any, Any]:
    return (clip.get("scene_id"), clip.get("beat_id"), clip.get("ordinal"))


def _dialogue_text_for_video_clip(clip: dict[str, Any], spec: dict[str, Any]) -> str:
    key = _scene_beat_key(clip)
    matches = [_clips_by_scene_beat(spec, t).get(key) for t in ("dialogue", "subtitle")]
    primary = next((item for item in matches if item), {})
    beat_type = str(clip.get("beat_type") or primary.get("beat_type") or "").lower()
    if beat_type and beat_type != "dialogue":
        return ""
    if not _strip_text(primary.get("speaker_name")):
        return ""
    for matched in matches:
        if not matched:
            continue
        text = _strip_text(matched.get("text"))
        if text:
            return text
    return ""


def _strip_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""
