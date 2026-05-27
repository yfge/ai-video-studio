from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TimelineShot(BaseModel):
    clip_id: str
    duration_ms: int = Field(..., ge=1)
    plot: str = Field(..., min_length=1)
    dialogue_source: str = Field(..., min_length=1)
    visual_prompt: str = Field(..., min_length=1)
    video_prompt: str = Field(..., min_length=1)
    character_anchor: str = Field(..., min_length=1)
    camera: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)


class TimelineShotPlan(BaseModel):
    shots: list[TimelineShot] = Field(..., min_length=1)


SHOT_PLAN_SCHEMA = TimelineShotPlan.model_json_schema()


def build_timeline_shot_plan_prompt(spec: dict[str, Any], *, style: str) -> str:
    clips = _timeline_prompt_clips(spec)
    return (
        "Return only valid JSON. Generate a Timeline-native shot plan for every "
        "video clip below. Do not change clip_id, timing, or duration_ms. Use only "
        "the provided Timeline fields as story source. The output schema is: "
        '{"shots":[{"clip_id":str,"duration_ms":int,"plot":str,'
        '"dialogue_source":str,"visual_prompt":str,"video_prompt":str,'
        '"character_anchor":str,"camera":str,"action":str}]}. '
        f"Style must be {style}; use non-real cartoon characters only. "
        "Use the same protagonist anchor across all shots when character_anchor_hint "
        "is present. character_anchor must be a reusable visual descriptor, not only "
        "a bare character name. Supporting characters may appear only as secondary "
        "props/figures and must not replace the protagonist. "
        "Each video_prompt must include plot, dialogue_source, character_anchor, "
        "camera, action, style, and duration. Timeline clips: "
        f"{clips}"
    )


def validate_timeline_shot_plan_matches(
    plan: dict[str, Any],
    spec: dict[str, Any],
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
        expected = int(video_by_id[clip_id].get("duration_ms") or 0)
        if int(shot.get("duration_ms") or 0) != expected:
            return {
                "message": "timeline shot plan duration mismatch",
                "clip_id": clip_id,
                "expected_duration_ms": expected,
                "actual_duration_ms": shot.get("duration_ms"),
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


def _timeline_prompt_clips(spec: dict[str, Any]) -> list[dict[str, Any]]:
    dialogue_by_key = _clips_by_scene_beat(spec, "dialogue")
    subtitle_by_key = _clips_by_scene_beat(spec, "subtitle")
    prompt_clips: list[dict[str, Any]] = []
    for clip in clips_for_track(spec, "video"):
        key = _scene_beat_key(clip)
        dialogue_clip = dialogue_by_key.get(key) or {}
        subtitle_clip = subtitle_by_key.get(key) or {}
        source_refs = clip.get("source_refs") if isinstance(clip, dict) else {}
        if not isinstance(source_refs, dict):
            source_refs = {}
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
