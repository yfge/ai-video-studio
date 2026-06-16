#!/usr/bin/env python3
"""Run a harness golden-path scenario."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any

import requests

if __package__ in {None, ""}:
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from scripts.harness._common import (
    ensure_run_dir,
    standard_fields,
    update_summary,
    write_json,
)
from scripts.harness.scenarios import GOLDEN_PATH_SCENARIOS
from scripts.harness.timeline_export_flow import run_timeline_export_flow


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", required=True, choices=sorted(GOLDEN_PATH_SCENARIOS))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--base-url", default="http://localhost:8089")
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--username", default=os.getenv("HARNESS_USER", "geyunfei"))
    parser.add_argument("--password", default=os.getenv("HARNESS_PASSWORD", "Gyf@845261"))
    parser.add_argument("--script-id", default=os.getenv("HARNESS_SCRIPT_ID", ""))
    parser.add_argument("--virtual-ip-id", default=os.getenv("HARNESS_VIRTUAL_IP_ID", ""))
    parser.add_argument("--timeout-seconds", type=int, default=180)
    return parser.parse_args()


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


def login(session: requests.Session, args: argparse.Namespace, chain: list[dict[str, Any]]) -> dict[str, Any]:
    response = session.post(
        f"{args.api_url.rstrip('/')}/api/v1/auth/login",
        data={"username": args.username, "password": args.password},
        headers={"x-harness-run-id": args.run_id, "x-client-request-id": f"{args.run_id}-login"},
        timeout=15,
    )
    record_response(chain, response, label="login")
    response.raise_for_status()
    payload = response.json()
    session.headers["Authorization"] = f"Bearer {payload['access_token']}"
    session.headers["x-harness-run-id"] = args.run_id
    return payload


def poll_task(
    session: requests.Session,
    api_url: str,
    task_id: int,
    timeout_seconds: int,
    chain: list[dict[str, Any]],
) -> dict[str, Any]:
    deadline = time.time() + timeout_seconds
    last_payload: dict[str, Any] | None = None
    while time.time() < deadline:
        response = session.get(f"{api_url.rstrip('/')}/api/v1/tasks/{task_id}", timeout=15)
        record_response(chain, response, label=f"poll-task-{task_id}")
        response.raise_for_status()
        last_payload = response.json()
        status = str((last_payload or {}).get("status", "")).lower()
        if status in {"completed", "failed", "cancelled"}:
            return last_payload
        time.sleep(3)
    return last_payload or {"status": "timeout", "id": task_id}


def scenario_inputs(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "run_id": args.run_id, "api_url": args.api_url, "base_url": args.base_url,
        "script_id": args.script_id or None,
        "virtual_ip_id": args.virtual_ip_id or None, "timeout_seconds": args.timeout_seconds,
    }


def run_scenario(args: argparse.Namespace) -> dict[str, Any]:
    scenario = GOLDEN_PATH_SCENARIOS[args.scenario]
    session = requests.Session()
    request_chain: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    payload: dict[str, Any] = {
        **standard_fields("STD-EVIDENCE-001"),
        "contract_version": 2,
        "scenario": scenario.name,
        "description": scenario.description,
        "notes": scenario.notes,
        "input_snapshot": scenario_inputs(args),
        "request_chain": request_chain,
        "success_criteria": [],
        "failure_categories": [],
        "key_artifacts": {},
    }

    if scenario.requires_script_id and not args.script_id:
        payload["failure_categories"].append("missing_input")
        failures.append({"category": "missing_input", "detail": "HARNESS_SCRIPT_ID is required"})
        payload["failures"] = failures
        payload["ok"] = False
        return payload
    if scenario.requires_virtual_ip_id and not args.virtual_ip_id:
        payload["failure_categories"].append("missing_input")
        failures.append({"category": "missing_input", "detail": "HARNESS_VIRTUAL_IP_ID is required"})
        payload["failures"] = failures
        payload["ok"] = False
        return payload

    try:
        if scenario.name == "mock_smoke":
            response = session.get(f"{args.api_url.rstrip('/')}/health", timeout=10)
            record_response(request_chain, response, label="health")
            payload["health_status"] = response.json()
            payload["success_criteria"] = ["health endpoint returns 200", "response includes status=healthy"]
            payload["ok"] = response.ok and payload["health_status"].get("status") == "healthy"
        else:
            login_payload = login(session, args, request_chain)
            payload["key_artifacts"]["auth"] = {"token_type": login_payload.get("token_type")}
            me_response = session.get(f"{args.api_url.rstrip('/')}/api/v1/auth/me", timeout=10)
            record_response(request_chain, me_response, label="auth-me")
            me_response.raise_for_status()
            payload["auth_user"] = me_response.json().get("username")

            if scenario.name == "auth_login_and_me":
                payload["success_criteria"] = ["login returns access token", "/auth/me returns authenticated user"]
                payload["ok"] = bool(payload["auth_user"])

            elif scenario.name == "task_traceability":
                tasks_response = session.get(f"{args.api_url.rstrip('/')}/api/v1/tasks", timeout=10)
                record_response(request_chain, tasks_response, label="tasks-list")
                tasks_response.raise_for_status()
                tasks_payload = tasks_response.json()
                payload["tasks_count"] = len(tasks_payload.get("tasks", []))
                payload["success_criteria"] = ["authenticated task list is reachable", "request ids are captured in request chain"]
                payload["ok"] = tasks_response.ok

            elif scenario.name == "virtual_ip_image_generation_real_or_mock":
                image_response = session.post(
                    f"{args.api_url.rstrip('/')}/api/v1/virtual-ips/{args.virtual_ip_id}/images/generate",
                    json={"style": "realistic", "category": "portrait", "model_id": "mock-model"},
                    timeout=30,
                )
                record_response(request_chain, image_response, label="virtual-ip-image-generate")
                image_response.raise_for_status()
                image_payload = image_response.json()
                payload["key_artifacts"]["image"] = {
                    "virtual_ip_id": image_payload.get("virtual_ip_id"),
                    "file_path": image_payload.get("file_path"),
                    "category": image_payload.get("category"),
                    "ai_model": image_payload.get("ai_model"),
                }
                payload["success_criteria"] = ["image generation returns metadata", "generated file path is present"]
                payload["ok"] = bool(image_payload.get("file_path"))

            else:
                response = session.post(
                    f"{args.api_url.rstrip('/')}/api/v1/scripts/{args.script_id}/timeline-pipeline/generate-async",
                    json={
                        "overwrite_audio": False,
                        "overwrite_timeline": False,
                        "overwrite_storyboard": False,
                    },
                    timeout=15,
                )
                record_response(request_chain, response, label="timeline-pipeline-generate")
                response.raise_for_status()
                queue_payload = response.json()
                task_id = int(queue_payload["data"]["task_id"])
                payload["key_artifacts"]["task"] = {"task_id": task_id}
                task_payload = poll_task(
                    session,
                    args.api_url,
                    task_id,
                    args.timeout_seconds,
                    request_chain,
                )
                payload["task"] = task_payload
                status = str((task_payload or {}).get("status", "")).lower()
                result_ref = task_payload.get("result_file_path")

                if scenario.name == "episode_timeline_generation":
                    payload["success_criteria"] = ["timeline task is queued", "timeline task completes"]
                    payload["ok"] = status == "completed"
                else:
                    run_timeline_export_flow(
                        session=session,
                        api_url=args.api_url,
                        script_id=args.script_id,
                        timeout_seconds=args.timeout_seconds,
                        chain=request_chain,
                        payload=payload,
                        failures=failures,
                        task_status=status,
                        result_ref=result_ref,
                    )

        if not payload["ok"] and not failures:
            failures.append({"category": "assertion_failed", "detail": "scenario criteria not met"})
    except requests.RequestException as exc:
        failures.append({"category": "request_error", "detail": str(exc)})
        payload["ok"] = False
    except Exception as exc:  # pragma: no cover - defensive harness guard
        failures.append({"category": "unexpected_error", "detail": str(exc)})
        payload["ok"] = False

    payload["failure_categories"] = sorted({item["category"] for item in failures})
    payload["failures"] = failures
    return payload


def main() -> int:
    args = parse_args()
    run_dir = ensure_run_dir(args.run_id)
    result = run_scenario(args)
    write_json(run_dir / "golden_path.json", result)
    update_summary(
        run_dir,
        **standard_fields("STD-EVIDENCE-001"),
        golden_path=result["scenario"],
        golden_path_status="passed" if result.get("ok") else "failed",
        task_id=((result.get("task") or {}).get("id") if result.get("task") else None),
    )
    print(json.dumps({"ok": result.get("ok", False), "scenario": result["scenario"]}))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
