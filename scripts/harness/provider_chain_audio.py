"""Dialogue audio generation helpers for provider-chain regression."""

from __future__ import annotations

import argparse
from typing import Any

import requests

from scripts.harness.provider_chain_api import request_json

TTS_MODEL = "speech-2.6-hd"
TTS_PROVIDER = "minimax"


def generate_dialogue_audio_for_timeline(
    session: requests.Session,
    args: argparse.Namespace,
    timeline: dict[str, Any],
    payload: dict[str, Any],
) -> dict[str, Any]:
    clips = _dialogue_clips(timeline.get("spec") or {})
    if not clips:
        raise RuntimeError("timeline_dialogue_text_missing")
    audio_clips = []
    for index, clip in enumerate(clips, start=1):
        text = str(clip.get("text") or "").strip()
        if not text:
            raise RuntimeError(f"timeline_dialogue_clip_{index}_text_missing")
        body = request_json(
            session,
            "POST",
            f"{args.api_url.rstrip('/')}/api/v1/voice/tts",
            json={
                "text": text,
                "model": TTS_MODEL,
                "provider": TTS_PROVIDER,
                "output_format": "url",
                "format": "mp3",
                "channel": 2,
                "speed": 1.0,
            },
            chain=payload["request_chain"],
            label=f"dialogue-tts-{index}",
            timeout=args.timeout_seconds,
        )
        data = body.get("data") or {}
        audio_url = data.get("audio_url")
        if not isinstance(audio_url, str) or not audio_url.startswith(
            ("http://", "https://")
        ):
            raise RuntimeError(f"dialogue_tts_{index}_missing_public_audio_url")
        audio_clips.append(
            {
                "clip_id": clip.get("clip_id"),
                "audio_url": audio_url,
                "text": text,
                "start_ms": clip.get("start_ms"),
                "end_ms": clip.get("end_ms"),
                "extra_info": data.get("extra_info"),
                "trace_id": data.get("trace_id"),
            }
        )
    artifact = {
        "provider": TTS_PROVIDER,
        "model": TTS_MODEL,
        "clip_count": len(audio_clips),
        "clips": audio_clips,
    }
    payload["key_artifacts"]["dialogue_audio"] = artifact
    return artifact


def _dialogue_clips(spec: dict[str, Any]) -> list[dict[str, Any]]:
    clips: list[dict[str, Any]] = []
    for track in spec.get("tracks") or []:
        if not isinstance(track, dict) or track.get("track_type") != "dialogue":
            continue
        for clip in track.get("clips") or []:
            if isinstance(clip, dict):
                clips.append(clip)
    return clips
