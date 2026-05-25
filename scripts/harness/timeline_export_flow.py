"""Harness helpers for Timeline render/export validation."""

from __future__ import annotations

import json
import time
from typing import Any

import requests


def record_response(
    chain: list[dict[str, Any]],
    response: requests.Response,
    *,
    label: str,
) -> None:
    chain.append(
        {
            "label": label,
            "method": response.request.method,
            "url": response.url,
            "status_code": response.status_code,
            "request_id": response.headers.get("x-request-id"),
            "harness_run_id": response.headers.get("x-harness-run-id"),
        }
    )


def poll_render_job(
    session: requests.Session,
    api_url: str,
    timeline_id: int,
    render_job_id: int,
    timeout_seconds: int,
    chain: list[dict[str, Any]],
) -> dict[str, Any]:
    deadline = time.time() + timeout_seconds
    last_payload: dict[str, Any] | None = None
    while time.time() < deadline:
        response = session.get(
            f"{api_url.rstrip('/')}/api/v1/timelines/{timeline_id}/render-jobs",
            timeout=15,
        )
        record_response(chain, response, label=f"poll-render-job-{render_job_id}")
        response.raise_for_status()
        jobs = response.json().get("items", [])
        last_payload = next(
            (job for job in jobs if int(job.get("id", 0)) == render_job_id),
            None,
        )
        status = str((last_payload or {}).get("status", "")).lower()
        if status in {"succeeded", "failed", "cancelled"}:
            return last_payload or {"status": "missing", "id": render_job_id}
        time.sleep(3)
    return last_payload or {"status": "timeout", "id": render_job_id}


def run_timeline_export_flow(
    *,
    session: requests.Session,
    api_url: str,
    script_id: str,
    timeout_seconds: int,
    chain: list[dict[str, Any]],
    payload: dict[str, Any],
    failures: list[dict[str, Any]],
    task_status: str,
    result_ref: Any,
) -> None:
    script_response = session.get(
        f"{api_url.rstrip('/')}/api/v1/scripts/{script_id}",
        timeout=15,
    )
    record_response(chain, script_response, label="script-read")
    script_response.raise_for_status()
    script_payload = script_response.json()
    episode_id = int(script_payload["episode_id"])
    timeline = _latest_script_timeline(
        session=session,
        api_url=api_url,
        episode_id=episode_id,
        script_id=script_id,
        chain=chain,
    )
    if timeline is None:
        failures.append(
            {
                "category": "missing_timeline",
                "detail": "timeline pipeline completed without a Timeline row",
            }
        )
        payload["ok"] = False
    else:
        _render_timeline(
            session=session,
            api_url=api_url,
            timeline=timeline,
            timeout_seconds=timeout_seconds,
            chain=chain,
            payload=payload,
            failures=failures,
            task_status=task_status,
        )

    payload["success_criteria"] = [
        "timeline task is queued",
        "timeline task completes",
        "timeline render job succeeds",
        "render job exposes output_asset file_url or file_path",
    ]
    if task_status == "completed" and result_ref:
        payload["key_artifacts"]["legacy_result_file_path"] = result_ref
    if task_status != "completed":
        failures.append(
            {
                "category": "timeline_task_failed",
                "detail": f"timeline pipeline ended with status={task_status}",
            }
        )


def _latest_script_timeline(
    *,
    session: requests.Session,
    api_url: str,
    episode_id: int,
    script_id: str,
    chain: list[dict[str, Any]],
) -> dict[str, Any] | None:
    timelines_response = session.get(
        f"{api_url.rstrip('/')}/api/v1/episodes/{episode_id}/timelines",
        timeout=15,
    )
    record_response(chain, timelines_response, label="timeline-list")
    timelines_response.raise_for_status()
    timelines = [
        item
        for item in timelines_response.json().get("items", [])
        if int(item.get("script_id", 0)) == int(script_id)
    ]
    return timelines[0] if timelines else None


def _render_timeline(
    *,
    session: requests.Session,
    api_url: str,
    timeline: dict[str, Any],
    timeout_seconds: int,
    chain: list[dict[str, Any]],
    payload: dict[str, Any],
    failures: list[dict[str, Any]],
    task_status: str,
) -> None:
    render_payload = _queue_timeline_render(
        session=session,
        api_url=api_url,
        timeline=timeline,
        chain=chain,
        force_new_attempt=False,
    )
    if str(render_payload.get("status", "")).lower() in {"failed", "cancelled"}:
        render_payload = _queue_timeline_render(
            session=session,
            api_url=api_url,
            timeline=timeline,
            chain=chain,
            force_new_attempt=True,
        )
    render_job = poll_render_job(
        session,
        api_url,
        int(timeline["id"]),
        int(render_payload["id"]),
        timeout_seconds,
        chain,
    )
    payload["key_artifacts"]["timeline"] = {
        "timeline_id": timeline["id"],
        "version": timeline["version"],
    }
    payload["key_artifacts"]["render_job"] = render_job

    render_status = str(render_job.get("status", "")).lower()
    output_asset = render_job.get("output_asset") or {}
    missing_clips = (render_job.get("log") or {}).get("missing_clips")
    payload["ok"] = (
        task_status == "completed"
        and render_status == "succeeded"
        and bool(output_asset.get("file_url") or output_asset.get("file_path"))
    )
    if render_status == "failed" and missing_clips:
        failures.append(
            {
                "category": "missing_clip_videos",
                "detail": f"render blocked by {len(missing_clips)} missing clips",
            }
        )
    elif render_status != "succeeded":
        failures.append(
            {
                "category": "render_failed",
                "detail": json.dumps(render_job.get("log") or {}, ensure_ascii=False),
            }
        )


def _queue_timeline_render(
    *,
    session: requests.Session,
    api_url: str,
    timeline: dict[str, Any],
    chain: list[dict[str, Any]],
    force_new_attempt: bool,
) -> dict[str, Any]:
    request_payload: dict[str, Any] = {
        "timeline_version": timeline["version"],
        "render_type": "final",
        "preset": {"fps": 24, "resolution": "1080x1920"},
    }
    if force_new_attempt:
        request_payload["force_new_attempt"] = True
    render_response = session.post(
        f"{api_url.rstrip('/')}/api/v1/timelines/{timeline['id']}/render",
        json=request_payload,
        timeout=15,
    )
    record_response(
        chain,
        render_response,
        label="timeline-render-retry" if force_new_attempt else "timeline-render",
    )
    render_response.raise_for_status()
    return render_response.json()
