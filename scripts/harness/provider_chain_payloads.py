"""Payload helpers for provider chain regression."""

from __future__ import annotations

import json
import re
from copy import deepcopy
from typing import Any

TEXT_MODEL = "deepseek-v4-flash"
IMAGE_MODEL = "openai:chatgpt-img-2"
VIDEO_MODEL = "seedance-2.0-i2v"
SEEDANCE_CANONICAL = "doubao-seedance-2-0-260128"


def scene_durations(mode: str) -> list[int]:
    return [4] if mode == "smoke" else [15, 15]


def build_script_prompt(mode: str) -> str:
    durations = scene_durations(mode)
    return (
        "Return only valid JSON. Write a compact Chinese short-drama script for a "
        "non-real 3D cartoon robot character. No live-action human, no celebrity, "
        "no photorealistic face. The JSON schema is: "
        '{"title":str,"logline":str,"characters":[{"name":str,"role":str,'
        '"appearance_prompt":str,"consistency_anchor":str}],'
        '"scenes":[{"scene_id":str,"duration_seconds":int,"plot":str,'
        '"dialogue":[{"speaker":str,"line":str}],"image_prompt":str,'
        '"video_prompt":str}]}. '
        f"Create exactly {len(durations)} scene(s) with durations {durations}. "
        "Every scene must have plot, at least one dialogue line, and a Seedance-ready "
        "video prompt that includes the character anchor and the dialogue source."
    )


def extract_structured_script(content: str, expected_scene_count: int) -> dict[str, Any]:
    text = content.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S)
    if fence:
        text = fence.group(1)
    elif not text.startswith("{"):
        match = re.search(r"\{.*\}", text, flags=re.S)
        if match:
            text = match.group(0)

    data = json.loads(text)
    scenes = data.get("scenes")
    characters = data.get("characters")
    if not isinstance(characters, list) or not characters:
        raise ValueError("script_missing_characters")
    if not isinstance(scenes, list) or len(scenes) != expected_scene_count:
        raise ValueError("script_scene_count_mismatch")

    for index, scene in enumerate(scenes, start=1):
        dialogue = scene.get("dialogue")
        if not scene.get("plot") or not scene.get("video_prompt"):
            raise ValueError(f"script_scene_{index}_missing_plot_or_video_prompt")
        if not isinstance(dialogue, list) or not dialogue:
            raise ValueError(f"script_scene_{index}_missing_dialogue")
        for line in dialogue:
            if (
                not isinstance(line, dict)
                or not line.get("speaker")
                or not line.get("line")
            ):
                raise ValueError(f"script_scene_{index}_invalid_dialogue")
    return data


def character_image_prompt(script: dict[str, Any]) -> str:
    character = script["characters"][0]
    return (
        f"{character.get('appearance_prompt', '')}. "
        f"{character.get('consistency_anchor', '')}. "
        "High quality 3D cartoon character reference sheet, expressive LED eyes, "
        "cinematic lighting, clean silhouette, non-real robot, no photorealistic human."
    )


def video_prompt(scene: dict[str, Any], character: dict[str, Any]) -> str:
    dialogue = " / ".join(f"{d['speaker']}: {d['line']}" for d in scene["dialogue"])
    return (
        f"{scene.get('video_prompt')}. "
        f"Character anchor: {character.get('consistency_anchor')}. "
        f"Plot: {scene.get('plot')}. Dialogue source: {dialogue}. "
        "3D cartoon style, non-real robot character, clear acting, readable story beat."
    )


def build_timeline_seed_spec(
    run_id: str,
    episode_id: int,
    script_id: int,
    script: dict[str, Any],
    image_url: str | None = None,
) -> dict[str, Any]:
    character = script["characters"][0]
    cursor = 0
    video_clips: list[dict[str, Any]] = []
    for ordinal, scene in enumerate(script["scenes"], start=1):
        duration = int(scene.get("duration_seconds") or scene_durations("smoke")[0])
        duration_ms = duration * 1000
        start_ms, end_ms = cursor, cursor + duration_ms
        cursor = end_ms
        scene_id = str(scene.get("scene_id") or f"scene_{ordinal}")
        beat_id = f"provider_chain_{ordinal}"
        clip_id = f"video_{scene_id}_{beat_id}_{ordinal:03d}".replace("-", "_")
        prompt = video_prompt(scene, character)
        video_clips.append(
            {
                "clip_id": clip_id,
                "track_type": "video",
                "scene_id": scene_id,
                "beat_id": beat_id,
                "ordinal": ordinal,
                "start_ms": start_ms,
                "end_ms": end_ms,
                "duration_ms": duration_ms,
                "source": {
                    "kind": "manual",
                    "provider_chain_run_id": run_id,
                    "timeline_first": True,
                },
                "source_refs": {
                    "provider_chain_run_id": run_id,
                    "provider_chain_stage": "timeline_seed",
                    "dialogue": scene.get("dialogue"),
                    "image_url": image_url,
                    "script_scene": scene,
                    "video_prompt": prompt,
                },
                "placeholder": True,
                "text": scene.get("plot"),
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
        "tracks": [{"track_type": "video", "clips": video_clips}],
    }


def attach_timeline_video_assets(
    seed_spec: dict[str, Any],
    clips: list[dict[str, Any]],
    run_id: str,
) -> dict[str, Any]:
    spec = deepcopy(seed_spec)
    generated_by_id = {clip.get("clip_id"): clip for clip in clips}
    attached_ids: set[str] = set()
    missing_ids: list[str] = []
    for track in spec.get("tracks") or []:
        if not isinstance(track, dict) or track.get("track_type") != "video":
            continue
        for clip in track.get("clips") or []:
            if not isinstance(clip, dict):
                continue
            generated = generated_by_id.get(clip.get("clip_id"))
            if not generated:
                missing_ids.append(str(clip.get("clip_id")))
                continue
            attached_ids.add(str(clip.get("clip_id")))
            clip["placeholder"] = False
            clip["video_url"] = generated["video_url"]
            clip["asset_ref"] = {
                "kind": "provider_chain_video",
                "url": generated["video_url"],
                "file_url": generated["video_url"],
                "provider": generated["provider"],
                "model": generated["model"],
                "task_id": generated.get("task_id"),
            }
            refs = clip.setdefault("source_refs", {})
            refs.update(
                {
                    "provider_chain_run_id": run_id,
                    "provider_chain_stage": "video_generated",
                    "image_url": generated.get("image_url"),
                    "video_url": generated["video_url"],
                    "task_id": generated.get("task_id"),
                    "provider": generated["provider"],
                    "model": generated["model"],
                }
            )
    unused_ids = {str(clip_id) for clip_id in generated_by_id if clip_id not in attached_ids}
    if missing_ids or unused_ids:
        raise RuntimeError(
            "timeline_asset_lineage_mismatch: "
            f"missing={sorted(missing_ids)} unused={sorted(unused_ids)}"
        )
    return spec


def mark_quality(payload: dict[str, Any], clips: list[dict[str, Any]], image_url: str) -> None:
    checks = {
        "has_character_image_url": bool(image_url),
        "all_clips_have_dialogue_source": all(c["scene"].get("dialogue") for c in clips),
        "all_clips_have_video_prompt": all(c.get("prompt") for c in clips),
        "all_clips_have_lineage": all(c.get("task_id") and c.get("video_url") for c in clips),
    }
    payload["production_quality"] = {"ok": all(checks.values()), "checks": checks}
    if not payload["production_quality"]["ok"]:
        raise RuntimeError("production_quality_failed")
