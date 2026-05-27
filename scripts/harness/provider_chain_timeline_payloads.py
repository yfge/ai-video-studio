"""Timeline payload helpers for provider-chain regression."""

from __future__ import annotations

from typing import Any

from scripts.harness.provider_chain_payloads import scene_durations


def dialogue_text(scene: dict[str, Any]) -> str:
    return "\n".join(f"{d['speaker']}: {d['line']}" for d in scene["dialogue"])


def build_timeline_seed_spec(
    run_id: str,
    episode_id: int,
    script_id: int,
    script: dict[str, Any],
    image_url: str | None = None,
) -> dict[str, Any]:
    cursor = 0
    tracks = {"dialogue": [], "video": [], "subtitle": []}
    character = _primary_character(script)
    for ordinal, scene in enumerate(script["scenes"], start=1):
        duration = int(scene.get("duration_seconds") or scene_durations("smoke")[0])
        start_ms, end_ms = cursor, cursor + duration * 1000
        cursor = end_ms
        scene_id = str(scene.get("scene_id") or f"scene_{ordinal}")
        beat_id = f"provider_chain_{ordinal}"
        source = _source(run_id)
        refs = _source_refs(run_id, scene, image_url, character)
        dialogue = dialogue_text(scene)
        tracks["dialogue"].append(
            {
                **_clip_timing(
                    "dialogue", scene_id, beat_id, ordinal, start_ms, end_ms
                ),
                "source": dict(source),
                "source_refs": dict(refs),
                "text": dialogue,
                "speaker": scene["dialogue"][0]["speaker"],
            }
        )
        tracks["video"].append(
            {
                **_clip_timing("video", scene_id, beat_id, ordinal, start_ms, end_ms),
                "source": dict(source),
                "source_refs": dict(refs),
                "placeholder": True,
                "text": scene.get("plot"),
            }
        )
        tracks["subtitle"].append(
            {
                **_clip_timing(
                    "subtitle", scene_id, beat_id, ordinal, start_ms, end_ms
                ),
                "source": dict(source),
                "source_refs": dict(refs),
                "text": dialogue,
                "style": {"position": "bottom", "safe_area": True},
            }
        )
    return {
        "spec_version": "timeline.v1",
        "episode_id": episode_id,
        "script_id": script_id,
        "version": 1,
        "source_audio_timeline_version": 1,
        "fps": 24,
        "resolution": "1080x1920",
        "duration_ms": cursor,
        "source": {
            "type": "provider_chain_regression",
            "run_id": run_id,
            "timeline_first": True,
        },
        "tracks": [
            {"track_type": "dialogue", "clips": tracks["dialogue"]},
            {"track_type": "video", "clips": tracks["video"]},
            {"track_type": "subtitle", "clips": tracks["subtitle"]},
        ],
    }


def timeline_track_counts(spec: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for track in spec.get("tracks") or []:
        if not isinstance(track, dict):
            continue
        track_type = str(track.get("track_type") or track.get("type") or "")
        counts[track_type] = len(track.get("clips") or [])
    return counts


def mark_quality(
    payload: dict[str, Any],
    clips: list[dict[str, Any]],
    image_url: str,
    timeline: dict[str, Any],
) -> None:
    spec = timeline.get("spec") if isinstance(timeline.get("spec"), dict) else {}
    track_counts = timeline_track_counts(spec)
    checks = {
        "has_character_image_url": bool(image_url),
        "all_clips_have_dialogue_source": all(
            c.get("timeline_shot_plan", {}).get("dialogue_source") for c in clips
        ),
        "all_clips_have_video_prompt": all(c.get("prompt") for c in clips),
        "all_clips_have_lineage": all(
            c.get("task_id") and c.get("video_url") for c in clips
        ),
        "timeline_has_dialogue_track": track_counts.get("dialogue") == len(clips),
        "timeline_has_subtitle_track": track_counts.get("subtitle") == len(clips),
        "timeline_has_video_track": track_counts.get("video") == len(clips),
        "all_subtitle_clips_have_text": all(
            c.get("text") for c in _track_clips(spec, "subtitle")
        ),
        "all_dialogue_clips_have_text": all(
            c.get("text") for c in _track_clips(spec, "dialogue")
        ),
        "timeline_has_dialogue_audio": all(
            (c.get("asset_ref") or {}).get("url")
            for c in _track_clips(spec, "dialogue")
        ),
        "timeline_has_shot_plan": all(
            ((c.get("source_refs") or {}).get("timeline_shot_plan") or {}).get(
                "video_prompt"
            )
            for c in _track_clips(spec, "video")
        ),
    }
    payload["production_quality"] = {
        "ok": all(checks.values()),
        "checks": checks,
        "timeline_track_counts": track_counts,
    }
    if not payload["production_quality"]["ok"]:
        raise RuntimeError("production_quality_failed")


def _source(run_id: str) -> dict[str, Any]:
    return {
        "kind": "manual",
        "provider_chain_run_id": run_id,
        "timeline_first": True,
    }


def _source_refs(
    run_id: str,
    scene: dict[str, Any],
    image_url: str | None,
    character: dict[str, Any],
) -> dict[str, Any]:
    return {
        "provider_chain_run_id": run_id,
        "provider_chain_stage": "timeline_seed",
        "dialogue": scene.get("dialogue"),
        "plot": scene.get("plot"),
        "image_url": image_url,
        "character_name": character.get("name"),
        "character_role": character.get("role"),
        "character_appearance_prompt": character.get("appearance_prompt"),
        "character_anchor_hint": character.get("consistency_anchor"),
    }


def _clip_timing(
    track_type: str,
    scene_id: str,
    beat_id: str,
    ordinal: int,
    start_ms: int,
    end_ms: int,
) -> dict[str, Any]:
    return {
        "clip_id": f"{track_type}_{scene_id}_{beat_id}_{ordinal:03d}".replace("-", "_"),
        "track_type": track_type,
        "scene_id": scene_id,
        "beat_id": beat_id,
        "ordinal": ordinal,
        "start_ms": start_ms,
        "end_ms": end_ms,
        "duration_ms": end_ms - start_ms,
    }


def _track_clips(spec: dict[str, Any], track_type: str) -> list[dict[str, Any]]:
    for track in spec.get("tracks") or []:
        if isinstance(track, dict) and track.get("track_type") == track_type:
            return [clip for clip in track.get("clips") or [] if isinstance(clip, dict)]
    return []


def _primary_character(script: dict[str, Any]) -> dict[str, Any]:
    characters = script.get("characters")
    if isinstance(characters, list) and characters and isinstance(characters[0], dict):
        return characters[0]
    return {}
