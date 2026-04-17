#!/usr/bin/env python3
"""Run a harness golden-path scenario."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

import requests

if __package__ in {None, ""}:
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from scripts.harness._common import ensure_run_dir, update_summary, write_json
from scripts.harness.scenarios import GOLDEN_PATH_SCENARIOS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenario", required=True, choices=sorted(GOLDEN_PATH_SCENARIOS)
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--base-url", default="http://localhost:8089")
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--username", default=os.getenv("HARNESS_USER", "geyunfei"))
    parser.add_argument(
        "--password", default=os.getenv("HARNESS_PASSWORD", "Gyf@845261")
    )
    parser.add_argument("--script-id", default=os.getenv("HARNESS_SCRIPT_ID", ""))
    parser.add_argument("--timeout-seconds", type=int, default=180)
    return parser.parse_args()


def login(session: requests.Session, args: argparse.Namespace, run_id: str) -> str:
    response = session.post(
        f"{args.api_url.rstrip('/')}/api/v1/auth/login",
        data={"username": args.username, "password": args.password},
        headers={"x-harness-run-id": run_id, "x-client-request-id": f"{run_id}-login"},
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    token = payload["access_token"]
    session.headers["Authorization"] = f"Bearer {token}"
    session.headers["x-harness-run-id"] = run_id
    return token


def poll_task(
    session: requests.Session, api_url: str, task_id: int, timeout_seconds: int
) -> dict[str, object]:
    deadline = time.time() + timeout_seconds
    last_payload: dict[str, object] | None = None
    while time.time() < deadline:
        response = session.get(
            f"{api_url.rstrip('/')}/api/v1/tasks/{task_id}", timeout=15
        )
        response.raise_for_status()
        last_payload = response.json()
        status = (((last_payload or {}).get("status")) or "").lower()
        if status in {"completed", "failed", "cancelled"}:
            return last_payload
        time.sleep(3)
    return last_payload or {"status": "timeout", "id": task_id}


def main() -> int:
    args = parse_args()
    run_dir = ensure_run_dir(args.run_id)
    session = requests.Session()
    result: dict[str, object] = {
        "scenario": args.scenario,
        "description": GOLDEN_PATH_SCENARIOS[args.scenario]["description"],
    }

    if args.scenario == "mock_smoke":
        response = session.get(f"{args.api_url.rstrip('/')}/health", timeout=10)
        result["health_status"] = response.json()
        ok = response.ok
    else:
        login(session, args, args.run_id)
        me_response = session.get(
            f"{args.api_url.rstrip('/')}/api/v1/auth/me", timeout=10
        )
        me_response.raise_for_status()
        result["auth_user"] = me_response.json().get("username")
        ok = True

        if args.scenario == "operator_smoke":
            tasks_response = session.get(
                f"{args.api_url.rstrip('/')}/api/v1/tasks", timeout=10
            )
            tasks_response.raise_for_status()
            result["tasks_status"] = tasks_response.status_code

        if args.scenario == "timeline_export_regression":
            if not args.script_id:
                result["error"] = (
                    "HARNESS_SCRIPT_ID is required for timeline_export_regression"
                )
                ok = False
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
                response.raise_for_status()
                payload = response.json()
                task_id = int(payload["data"]["task_id"])
                result["task_id"] = task_id
                task_payload = poll_task(
                    session, args.api_url, task_id, args.timeout_seconds
                )
                result["task"] = task_payload
                status = (((task_payload or {}).get("status")) or "").lower()
                result["coverage_gap"] = (
                    "Current regression covers timeline pipeline completion; render/export "
                    "assertions still need dedicated media-asset contracts."
                )
                ok = status == "completed"

    write_json(run_dir / "golden_path.json", result)
    update_summary(
        run_dir,
        golden_path=args.scenario,
        golden_path_status="passed" if ok else "failed",
        task_id=result.get("task_id"),
    )
    print(json.dumps({"ok": ok, "scenario": args.scenario, "result": result}))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
