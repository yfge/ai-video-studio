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
    text = _dialogue_text(timeline.get("spec") or {})
    if not text:
        raise RuntimeError("timeline_dialogue_text_missing")
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
        label="dialogue-tts",
        timeout=args.timeout_seconds,
    )
    data = body.get("data") or {}
    audio_url = data.get("audio_url")
    if not isinstance(audio_url, str) or not audio_url.startswith(("http://", "https://")):
        raise RuntimeError("dialogue_tts_missing_public_audio_url")
    artifact = {
        "provider": TTS_PROVIDER,
        "model": TTS_MODEL,
        "audio_url": audio_url,
        "text": text,
        "extra_info": data.get("extra_info"),
        "trace_id": data.get("trace_id"),
    }
    payload["key_artifacts"]["dialogue_audio"] = artifact
    return artifact


def _dialogue_text(spec: dict[str, Any]) -> str:
    lines: list[str] = []
    for track in spec.get("tracks") or []:
        if not isinstance(track, dict) or track.get("track_type") != "dialogue":
            continue
        for clip in track.get("clips") or []:
            if isinstance(clip, dict) and isinstance(clip.get("text"), str):
                text = clip["text"].strip()
                if text:
                    lines.append(text)
    return "\n".join(lines)
