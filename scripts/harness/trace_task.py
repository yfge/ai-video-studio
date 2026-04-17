#!/usr/bin/env python3
"""Collect log and artifact evidence for a task id."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from scripts.harness._common import (
    ARTIFACTS_ROOT,
    find_jsonl_log,
    read_json,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    task_id = str(args.task_id)
    matching_runs = []
    for summary_path in sorted(ARTIFACTS_ROOT.glob("*/summary.json")):
        summary = read_json(summary_path, default={}) or {}
        if str(summary.get("task_id", "")) == task_id:
            matching_runs.append(
                {
                    "run_id": summary_path.parent.name,
                    "summary": summary,
                    "path": str(summary_path),
                }
            )

    logs = []
    log_path = find_jsonl_log()
    if log_path.exists():
        for raw_line in log_path.read_text(encoding="utf-8").splitlines():
            if task_id in raw_line:
                logs.append(json.loads(raw_line))

    output_path = ARTIFACTS_ROOT / f"task-{task_id}.json"
    payload = {"task_id": task_id, "matching_runs": matching_runs, "logs": logs[-50:]}
    write_json(output_path, payload)
    print(json.dumps({"ok": True, "path": str(output_path)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
