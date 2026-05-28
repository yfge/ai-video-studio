#!/usr/bin/env python3
"""Run the real provider chain through system APIs."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

import requests

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from scripts.harness._common import ensure_run_dir, update_summary, write_json
from scripts.harness.provider_chain_api import (
    confirm_models,
    create_virtual_ip,
    generate_character_image,
    generate_script,
    login,
)
from scripts.harness.provider_chain_audio import generate_dialogue_audio_for_timeline
from scripts.harness.provider_chain_media import generate_videos_for_timeline
from scripts.harness.provider_chain_payloads import scene_durations
from scripts.harness.provider_chain_render_probe import probe_render_output
from scripts.harness.provider_chain_timeline_payloads import mark_quality
from scripts.harness.provider_chain_timeline import (
    cleanup_virtual_ip,
    create_seed_timeline,
    generate_timeline_shot_plan,
    render_timeline,
    update_timeline_with_assets,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["smoke", "full-30s"], default="smoke")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--username", default=os.getenv("HARNESS_USER", "geyunfei"))
    parser.add_argument("--password", default=os.getenv("HARNESS_PASSWORD", "Gyf@845261"))
    parser.add_argument("--episode-id", type=int, default=_env_int("HARNESS_EPISODE_ID"))
    parser.add_argument("--script-id", type=int, default=_env_int("HARNESS_SCRIPT_ID"))
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--poll-interval-seconds", type=float, default=5.0)
    parser.add_argument("--video-concurrency", type=int, default=2)
    parser.add_argument(
        "--script-premise",
        default=None,
        help="Optional premise used only to vary the DeepSeek script seed.",
    )
    parser.add_argument("--keep-temp-ip", action="store_true")
    return parser.parse_args()


def _env_int(name: str) -> int | None:
    value = os.getenv(name)
    return int(value) if value else None


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "contract_version": 1,
        "scenario": "provider_chain_regression",
        "mode": args.mode,
        "input_snapshot": {
            "api_url": args.api_url,
            "username": args.username,
            "episode_id": args.episode_id,
            "script_id": args.script_id,
            "scene_durations": scene_durations(args.mode),
            "script_premise": args.script_premise,
        },
        "request_chain": [],
        "key_artifacts": {},
        "failures": [],
        "failure_categories": [],
    }


def run(args: argparse.Namespace, payload: dict[str, Any]) -> None:
    with requests.Session() as session:
        login(session, args, payload)
        confirm_models(session, args, payload)
        script = generate_script(session, args, payload)
        timeline = create_seed_timeline(session, args, script, payload)
        timeline = generate_timeline_shot_plan(session, args, timeline, payload)
        dialogue_audio = generate_dialogue_audio_for_timeline(
            session, args, timeline, payload
        )
        vip = create_virtual_ip(session, args, timeline, payload)
        try:
            image = generate_character_image(session, args, timeline, vip, payload)
            clips = generate_videos_for_timeline(session, args, timeline, image, payload)
            updated = update_timeline_with_assets(
                session,
                args,
                timeline,
                clips,
                payload,
                dialogue_audio=dialogue_audio,
            )
            mark_quality(payload, clips, image["image_url"], updated)
            render_timeline(session, args, updated, payload)
            probe_render_output(args, payload)
        finally:
            cleanup_virtual_ip(session, args, payload)


def main() -> int:
    args = parse_args()
    run_dir = ensure_run_dir(args.run_id)
    artifact = run_dir / "provider_chain.json"
    payload = build_payload(args)
    ok = False
    try:
        run(args, payload)
        ok = True
        return 0
    except Exception as exc:  # noqa: BLE001 - harness must persist failure evidence
        failure_message = f"{type(exc).__name__}: {exc}"
        payload["failures"].append({"type": type(exc).__name__, "message": str(exc)})
        payload["failure_categories"].append(_failure_category(failure_message, payload))
        return 1
    finally:
        payload["ok"] = ok
        write_json(artifact, payload)
        update_summary(
            run_dir,
            scenario="provider_chain_regression",
            mode=args.mode,
            ok=ok,
            provider_chain_artifact=str(artifact),
        )
        print({"ok": ok, "mode": args.mode, "artifact": str(artifact)})


def _failure_category(message: str, payload: dict[str, Any] | None = None) -> str:
    evidence = _failure_evidence(message, payload)
    if any(
        marker in evidence
        for marker in (
            "AccountOverdueError",
            "overdue balance",
            "insufficient balance",
            "quota",
            "余额不足",
            "欠费",
        )
    ):
        return "provider_billing_or_quota_failed"
    if any(
        marker in evidence
        for marker in (
            "ConnectionError",
            "RemoteDisconnected",
            "Connection aborted",
            "ReadTimeout",
            "ConnectTimeout",
        )
    ):
        return "api_transport_failed"
    if "script" in message or "JSON" in message:
        return "script_generation_failed"
    if (
        "oss_url" in message
        or "image_generation" in message
        or "images/generate" in message
        or "AI图像生成失败" in message
    ):
        return "image_persistence_failed"
    if "virtual-ips" in message or "虚拟IP" in message:
        return "virtual_ip_failed"
    if "tts" in message or "audio" in message:
        return "dialogue_audio_failed"
    if "video" in message or "Seedance" in message or "provider/model" in message:
        return "seedance_generation_failed"
    if "ffprobe" in message or "frame_extract" in message or "render_media_probe" in message:
        return "render_media_probe_failed"
    if "timeline" in message or "render" in message:
        return "timeline_render_failed"
    if "production_quality" in message:
        return "production_quality_failed"
    return "unknown"


def _failure_evidence(message: str, payload: dict[str, Any] | None) -> str:
    parts = [message]
    for item in (payload or {}).get("request_chain") or []:
        if not isinstance(item, dict):
            continue
        body = item.get("response_body")
        if isinstance(body, str) and body:
            parts.append(body)
        error = item.get("error")
        if isinstance(error, str) and error:
            parts.append(error)
    return "\n".join(parts)


if __name__ == "__main__":
    sys.exit(main())
