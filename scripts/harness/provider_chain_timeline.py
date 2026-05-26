"""Timeline composition helpers for provider chain regression."""

from __future__ import annotations

import argparse
import time
from typing import Any

import requests

from scripts.harness.provider_chain_api import request_json
from scripts.harness.provider_chain_timeline_payloads import (
    attach_timeline_video_assets,
    build_timeline_seed_spec,
    timeline_track_counts,
)


TERMINAL_RENDER_STATUSES = {"succeeded", "failed", "cancelled"}


def create_seed_timeline(
    session: requests.Session,
    args: argparse.Namespace,
    script: dict[str, Any],
    payload: dict[str, Any],
) -> dict[str, Any]:
    if not args.episode_id or not args.script_id:
        raise RuntimeError("timeline-first regression requires --episode-id and --script-id")

    spec = build_timeline_seed_spec(args.run_id, args.episode_id, args.script_id, script)
    timeline = request_json(
        session,
        "POST",
        f"{args.api_url.rstrip('/')}/api/v1/episodes/{args.episode_id}/timelines",
        json={
            "script_id": args.script_id,
            "title": f"Provider chain regression {args.run_id}",
            "status": "ready",
            "spec": spec,
            "source_audio_timeline_version": 1,
        },
        chain=payload["request_chain"],
        label="timeline-create",
        timeout=60,
    )
    if not timeline.get("id") or timeline.get("version") != 1:
        raise RuntimeError("timeline_create_missing_identity")
    payload["key_artifacts"]["timeline_seed"] = {
        "id": timeline["id"],
        "version": timeline["version"],
        "duration_ms": spec["duration_ms"],
        "clip_count": sum(timeline_track_counts(spec).values()),
        "track_counts": timeline_track_counts(spec),
        "created_before_media_generation": True,
    }
    return timeline


def update_timeline_with_assets(
    session: requests.Session,
    args: argparse.Namespace,
    timeline: dict[str, Any],
    clips: list[dict[str, Any]],
    payload: dict[str, Any],
    dialogue_audio: dict[str, Any] | None = None,
) -> dict[str, Any]:
    spec = attach_timeline_video_assets(
        timeline["spec"],
        clips,
        args.run_id,
        dialogue_audio=dialogue_audio,
    )
    updated = request_json(
        session,
        "PATCH",
        f"{args.api_url.rstrip('/')}/api/v1/timelines/{timeline['id']}",
        json={
            "expected_version": timeline["version"],
            "status": "ready",
            "spec": spec,
            "source_audio_timeline_version": 1,
        },
        chain=payload["request_chain"],
        label="timeline-assets-update",
        timeout=60,
    )
    payload["key_artifacts"]["timeline"] = {
        "id": updated["id"],
        "seed_version": timeline["version"],
        "version": updated["version"],
        "duration_ms": updated["spec"]["duration_ms"],
        "clip_count": len(clips),
        "created_before_media_generation": True,
    }
    return updated


def render_timeline(
    session: requests.Session,
    args: argparse.Namespace,
    timeline: dict[str, Any],
    payload: dict[str, Any],
) -> dict[str, Any]:
    job = request_json(
        session,
        "POST",
        f"{args.api_url.rstrip('/')}/api/v1/timelines/{timeline['id']}/render",
        json={
            "timeline_version": timeline["version"],
            "render_type": "final",
            "preset": {"fps": 24, "resolution": "1080x1920", "run_id": args.run_id},
            "force_new_attempt": False,
        },
        chain=payload["request_chain"],
        label="timeline-render-queue",
        timeout=60,
    )
    result = poll_render_job(session, args, timeline["id"], job["id"], payload)
    payload["key_artifacts"]["render_job"] = result
    return result


def poll_render_job(
    session: requests.Session,
    args: argparse.Namespace,
    timeline_id: int,
    render_job_id: int,
    payload: dict[str, Any],
) -> dict[str, Any]:
    deadline = time.monotonic() + args.timeout_seconds
    last_job: dict[str, Any] | None = None
    poll_url = f"{args.api_url.rstrip('/')}/api/v1/timelines/{timeline_id}/render-jobs"
    while time.monotonic() < deadline:
        try:
            body = request_json(
                session,
                "GET",
                poll_url,
                params={"include_deleted": False},
                chain=payload["request_chain"],
                label="timeline-render-poll",
                timeout=30,
            )
        except requests.ConnectionError as exc:
            payload["request_chain"].append(
                {
                    "label": "timeline-render-poll",
                    "method": "GET",
                    "url": poll_url,
                    "error": repr(exc),
                }
            )
            time.sleep(args.poll_interval_seconds)
            continue
        items = body.get("items") or []
        last_job = next((item for item in items if item.get("id") == render_job_id), None)
        if last_job and last_job.get("status") in TERMINAL_RENDER_STATUSES:
            break
        time.sleep(args.poll_interval_seconds)

    if not last_job:
        raise RuntimeError("timeline_render_job_not_found")
    if last_job.get("status") != "succeeded":
        raise RuntimeError(f"timeline_render_not_succeeded: {last_job.get('status')}")

    output = last_job.get("output_asset") or {}
    output_url = output.get("file_url") or output.get("file_path")
    if not output_url:
        raise RuntimeError("timeline_render_missing_output_asset_url")
    return {
        "id": last_job.get("id"),
        "status": last_job.get("status"),
        "progress": last_job.get("progress"),
        "output_url": output_url,
        "log": last_job.get("log"),
    }


def cleanup_virtual_ip(
    session: requests.Session,
    args: argparse.Namespace,
    payload: dict[str, Any],
) -> None:
    vip = payload.get("key_artifacts", {}).get("virtual_ip") or {}
    vip_id = vip.get("id")
    if args.keep_temp_ip or not vip_id:
        return
    try:
        body = request_json(
            session,
            "DELETE",
            f"{args.api_url.rstrip('/')}/api/v1/virtual-ips/{vip_id}",
            chain=payload["request_chain"],
            label="virtual-ip-cleanup",
            timeout=30,
        )
        payload.setdefault("cleanup", {})["virtual_ip"] = body
    except Exception as exc:  # noqa: BLE001 - cleanup must not hide main result
        payload.setdefault("cleanup", {})["virtual_ip_error"] = str(exc)
