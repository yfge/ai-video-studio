#!/usr/bin/env python3
"""Aggregate harness metrics from JSONL logs."""

from __future__ import annotations

import argparse
import json
import sys

if __package__ in {None, ""}:
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from scripts.harness.observability import (
    filter_log_records,
    load_log_records,
    summarize_metrics,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id")
    parser.add_argument("--task-id")
    parser.add_argument("--route")
    parser.add_argument("--level")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    records = filter_log_records(
        load_log_records(),
        run_id=args.run_id,
        task_id=args.task_id,
        route=args.route,
        level=args.level,
    )
    print(json.dumps(summarize_metrics(records), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
