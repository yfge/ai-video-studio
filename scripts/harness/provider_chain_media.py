"""Media generation helpers for timeline-first provider chain regression."""

from __future__ import annotations

import argparse
from typing import Any

import requests

from scripts.harness.provider_chain_api import request_json
from scripts.harness.provider_chain_payloads import SEEDANCE_CANONICAL, VIDEO_MODEL


def generate_videos_for_timeline(
    session: requests.Session,
    args: argparse.Namespace,
    timeline: dict[str, Any],
    image: dict[str, Any],
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    clips: list[dict[str, Any]] = []
    for index, clip in enumerate(_video_clips(timeline.get("spec") or {}), start=1):
        refs = clip.get("source_refs") if isinstance(clip.get("source_refs"), dict) else {}
        prompt = str(refs.get("video_prompt") or clip.get("text") or "").strip()
        if not prompt:
            raise RuntimeError(f"timeline_clip_{index}_missing_video_prompt")
        duration = _duration_seconds(clip)
        body = request_json(
            session,
            "POST",
            f"{args.api_url.rstrip('/')}/api/v1/ai/generate/video",
            json={
                "prompt": prompt,
                "image_url": image["image_url"],
                "model": VIDEO_MODEL,
                "prefer_provider": "volcengine",
                "duration": duration,
                "fps": 24,
                "resolution": "720p",
            },
            chain=payload["request_chain"],
            label=f"seedance-video-{index}",
            timeout=args.timeout_seconds,
        )
        data = body.get("data") or {}
        video_clip = _validated_clip(data, clip, refs, prompt, duration, index, image)
        clips.append(video_clip)
    payload["key_artifacts"]["videos"] = clips
    return clips


def _video_clips(spec: dict[str, Any]) -> list[dict[str, Any]]:
    clips: list[dict[str, Any]] = []
    for track in spec.get("tracks") or []:
        if not isinstance(track, dict) or track.get("track_type") != "video":
            continue
        clips.extend(item for item in track.get("clips") or [] if isinstance(item, dict))
    return clips


def _duration_seconds(clip: dict[str, Any]) -> int:
    duration_ms = int(clip.get("duration_ms") or 0)
    if duration_ms <= 0:
        raise RuntimeError(f"timeline_clip_missing_duration: {clip.get('clip_id')}")
    return max(round(duration_ms / 1000), 1)


def _validated_clip(
    data: dict[str, Any],
    timeline_clip: dict[str, Any],
    refs: dict[str, Any],
    prompt: str,
    duration: int,
    index: int,
    image: dict[str, Any],
) -> dict[str, Any]:
    model = str(data.get("model") or "")
    video_url = data.get("video_url")
    if data.get("provider") != "volcengine" or SEEDANCE_CANONICAL not in model:
        raise RuntimeError(f"unexpected video provider/model: {data.get('provider')} {model}")
    if not isinstance(video_url, str) or not video_url.startswith(("http://", "https://")):
        raise RuntimeError(f"video_{index}_missing_video_url")
    return {
        "ordinal": index,
        "clip_id": timeline_clip.get("clip_id"),
        "duration_seconds": duration,
        "video_url": video_url,
        "image_url": image["image_url"],
        "provider": data.get("provider"),
        "model": model,
        "task_id": (data.get("metadata") or {}).get("task_id"),
        "prompt": prompt,
        "scene": refs.get("script_scene") or {"dialogue": refs.get("dialogue")},
    }
