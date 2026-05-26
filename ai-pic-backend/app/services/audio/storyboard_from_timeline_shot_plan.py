from __future__ import annotations

from typing import Any
from uuid import uuid4


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
    prompt_description = str(
        shot_plan.get("visual_prompt") or shot_plan.get("video_prompt") or description
    ).strip()
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
