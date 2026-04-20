#!/usr/bin/env python3
"""Collect artifact and log evidence for a harness run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from scripts.harness._common import (
    find_jsonl_log,
    read_json,
    resolve_run_dir,
    write_json,
)
from scripts.harness.observability import filter_log_records, load_log_records, summarize_metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_dir = resolve_run_dir(args.run_id)
    log_path = find_jsonl_log()
    matching_logs = filter_log_records(load_log_records(log_path), run_id=args.run_id)
    payload = {
        "run_id": args.run_id,
        "manifest": read_json(run_dir / "manifest.json", default={}),
        "summary": read_json(run_dir / "summary.json", default={}),
        "browser_flow": read_json(run_dir / "browser_flow.json", default={}),
        "golden_path": read_json(run_dir / "golden_path.json", default={}),
        "doctor": read_json(run_dir / "doctor.json", default={}),
        "dom_snapshot": read_json(run_dir / "dom_snapshot.json", default={}),
        "logs": matching_logs[-50:],
        "metrics": summarize_metrics(matching_logs),
    }
    write_json(run_dir / "trace-run.json", payload)
    print(json.dumps({"ok": True, "path": str(run_dir / "trace-run.json")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
