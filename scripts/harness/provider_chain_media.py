"""Media generation helpers for timeline-first provider chain regression."""

from __future__ import annotations

import argparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    clips_to_generate = list(enumerate(_video_clips(timeline.get("spec") or {}), start=1))
    concurrency = max(1, int(getattr(args, "video_concurrency", 1) or 1))
    started = time.monotonic()
    if concurrency > 1 and len(clips_to_generate) > 1:
        clips = _generate_video_clips_parallel(
            session=session,
            args=args,
            clips_to_generate=clips_to_generate,
            image=image,
            payload=payload,
        )
    else:
        clips = []
        for index, clip in clips_to_generate:
            video_clip = _generate_one_video_clip(
                session=session,
                args=args,
                image=image,
                timeline_clip=clip,
                index=index,
                chain=payload["request_chain"],
            )
            clips.append(video_clip)
    payload["key_artifacts"]["videos"] = clips
    payload["key_artifacts"]["video_generation"] = {
        "clip_count": len(clips),
        "concurrency": min(concurrency, max(len(clips_to_generate), 1)),
        "wall_time_seconds": round(time.monotonic() - started, 3),
    }
    return clips


def _generate_video_clips_parallel(
    *,
    session: requests.Session,
    args: argparse.Namespace,
    clips_to_generate: list[tuple[int, dict[str, Any]]],
    image: dict[str, Any],
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    concurrency = min(
        max(1, int(getattr(args, "video_concurrency", 1) or 1)),
        len(clips_to_generate),
    )
    results: dict[int, tuple[list[dict[str, Any]], dict[str, Any]]] = {}
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {
            executor.submit(
                _generate_one_video_clip_with_cloned_session,
                session,
                args,
                image,
                index,
                clip,
            ): index
            for index, clip in clips_to_generate
        }
        for future in as_completed(futures):
            index = futures[future]
            request_chain, clip_result = future.result()
            results[index] = (request_chain, clip_result)

    clips: list[dict[str, Any]] = []
    for index, _clip in clips_to_generate:
        request_chain, clip_result = results[index]
        payload["request_chain"].extend(request_chain)
        clips.append(clip_result)
    return clips


def _generate_one_video_clip_with_cloned_session(
    base_session: requests.Session,
    args: argparse.Namespace,
    image: dict[str, Any],
    index: int,
    timeline_clip: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    chain: list[dict[str, Any]] = []
    with requests.Session() as session:
        session.headers.update(base_session.headers)
        session.cookies.update(base_session.cookies)
        clip = _generate_one_video_clip(
            session=session,
            args=args,
            image=image,
            timeline_clip=timeline_clip,
            index=index,
            chain=chain,
        )
    return chain, clip


def _generate_one_video_clip(
    *,
    session: requests.Session,
    args: argparse.Namespace,
    image: dict[str, Any],
    timeline_clip: dict[str, Any],
    index: int,
    chain: list[dict[str, Any]],
) -> dict[str, Any]:
    refs = (
        timeline_clip.get("source_refs")
        if isinstance(timeline_clip.get("source_refs"), dict)
        else {}
    )
    shot_plan = refs.get("timeline_shot_plan")
    if not isinstance(shot_plan, dict):
        raise RuntimeError(f"timeline_clip_{index}_missing_timeline_shot_plan")
    prompt = str(shot_plan.get("video_prompt") or "").strip()
    if not prompt:
        raise RuntimeError(f"timeline_clip_{index}_missing_video_prompt")
    duration = _duration_seconds(timeline_clip)
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
        chain=chain,
        label=f"seedance-video-{index}",
        timeout=args.timeout_seconds,
    )
    data = body.get("data") or {}
    return _validated_clip(data, timeline_clip, shot_plan, prompt, duration, index, image)


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
    shot_plan: dict[str, Any],
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
        "timeline_shot_plan": shot_plan,
        "scene": {
            "plot": shot_plan.get("plot"),
            "dialogue": shot_plan.get("dialogue_source"),
        },
    }
