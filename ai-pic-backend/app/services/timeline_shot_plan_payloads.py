from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any

from app.services.timeline_shot_plan_context import (
    clips_for_track,
    overlapping_clips,
    strip_text,
    timed_text,
    unique_texts,
)
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
        "4) motion_timeline has 2-4 ordered action beats inside the clip duration "
        "and follows source_motion_timeline when it is provided, "
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
        source_text = strip_text(clip.get("text"))
        dialogue_text = _dialogue_text_for_video_clip(clip, spec)
        if source_text and not strip_text(shot.get("plot")):
            return {
                "message": "timeline shot plan plot missing",
                "clip_id": clip_id,
            }
        if dialogue_text and not strip_text(shot.get("dialogue_source")):
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


def _timeline_prompt_clips(
    spec: dict[str, Any],
    *,
    clip_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    prompt_clips: list[dict[str, Any]] = []
    for clip in clips_for_track(spec, "video"):
        if clip_ids is not None and str(clip.get("clip_id")) not in clip_ids:
            continue
        dialogue_clips = overlapping_clips(spec, clip, "dialogue")
        subtitle_clips = overlapping_clips(spec, clip, "subtitle")
        source_refs = clip.get("source_refs") or {}
        source_refs = source_refs if isinstance(source_refs, dict) else {}
        dialogue_events = [timed_text(item, clip) for item in dialogue_clips]
        source_ranges = [
            item
            for item in clip.get("source_beat_ranges") or []
            if isinstance(item, dict)
        ]
        prompt_clips.append(
            {
                "clip_id": clip.get("clip_id"),
                "scene_id": clip.get("scene_id"),
                "beat_id": clip.get("beat_id"),
                "ordinal": clip.get("ordinal"),
                "start_ms": clip.get("start_ms"),
                "end_ms": clip.get("end_ms"),
                "duration_ms": clip.get("duration_ms"),
                "plot": clip.get("text") or "",
                "dialogue": "\n".join(
                    unique_texts(
                        item.get("text") for item in [*dialogue_clips, *subtitle_clips]
                    )
                ),
                "dialogue_events": dialogue_events,
                "speaker_names": unique_texts(
                    item.get("speaker_name") for item in dialogue_clips
                ),
                "characters_involved": clip.get("characters_involved") or [],
                "source_beat_ranges": source_ranges,
                "source_motion_timeline": [
                    {
                        "at_ms": max(
                            0,
                            int(item.get("start_ms") or 0)
                            - int(clip.get("start_ms") or 0),
                        ),
                        "beat_type": item.get("beat_type"),
                        "action": item.get("text") or item.get("dialogue_action") or "",
                        "speaker_name": item.get("speaker_name"),
                    }
                    for item in source_ranges
                    if item.get("text") or item.get("dialogue_action")
                ],
                "character_name": source_refs.get("character_name"),
                "character_appearance_prompt": source_refs.get(
                    "character_appearance_prompt"
                ),
                "character_anchor_hint": source_refs.get("character_anchor_hint"),
            }
        )
    return prompt_clips


def _dialogue_text_for_video_clip(clip: dict[str, Any], spec: dict[str, Any]) -> str:
    matches = overlapping_clips(spec, clip, "dialogue")
    return "\n".join(
        unique_texts(
            item.get("text") for item in matches if strip_text(item.get("speaker_name"))
        )
    )
