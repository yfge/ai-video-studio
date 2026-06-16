#!/usr/bin/env python3
"""Run production-quality validation for timeline-first provider samples."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from scripts.harness._common import ensure_run_dir, update_summary
from scripts.harness.production_quality_live import run_live_samples
from scripts.harness.production_quality_report import (
    aggregate_quality_report,
    evaluate_provider_chain_sample,
    load_provider_chain,
    resolve_provider_chain_path,
    write_quality_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["audit-existing", "live-10"], required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--input-run", default=None)
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--username", default=os.getenv("HARNESS_USER", "geyunfei"))
    parser.add_argument("--password", default=os.getenv("HARNESS_PASSWORD", "Gyf@845261"))
    parser.add_argument("--episode-id", type=int, default=_env_int("HARNESS_EPISODE_ID"))
    parser.add_argument("--script-id", type=int, default=_env_int("HARNESS_SCRIPT_ID"))
    parser.add_argument("--sample-count", type=int, default=10)
    parser.add_argument("--duration-plan", default="15,15")
    parser.add_argument("--video-concurrency", type=int, default=2)
    parser.add_argument("--max-retries", type=int, default=1)
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--poll-interval-seconds", type=float, default=5.0)
    parser.add_argument("--keep-temp-ip", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_dir = ensure_run_dir(args.run_id)
    if args.duration_plan != "15,15":
        raise SystemExit("Only --duration-plan 15,15 is supported by full-30s today.")
    report = audit_existing(args) if args.mode == "audit-existing" else run_live_samples(args, run_dir)
    write_quality_outputs(run_dir, report)
    update_summary(
        run_dir,
        scenario="production_quality_regression",
        mode=args.mode,
        verdict=report.get("aggregate", {}).get("verdict"),
        standard_ids=report.get("aggregate", {}).get("covered_standard_ids"),
        quality_report=str(run_dir / "quality_report.json"),
        samples_csv=str(run_dir / "samples.csv"),
        review_pack=str(run_dir / "review_pack.md"),
    )
    print(
        {
            "ok": report.get("aggregate", {}).get("verdict") == "trial_ready",
            "mode": args.mode,
            "quality_report": str(run_dir / "quality_report.json"),
            "verdict": report.get("aggregate", {}).get("verdict"),
        }
    )
    return 0


def audit_existing(args: argparse.Namespace) -> dict[str, Any]:
    if not args.input_run:
        raise SystemExit("--input-run is required for audit-existing")
    payload = load_provider_chain(args.input_run)
    provider_chain_path = resolve_provider_chain_path(args.input_run)
    sample = evaluate_provider_chain_sample(
        payload,
        provider_chain_artifact=str(provider_chain_path),
        script_score={
            "status": "skipped",
            "reason": "audit_existing_is_read_only",
        },
        frame_artifacts=[],
        contact_sheet=None,
        sample_id="audit-existing-01",
        attempt=1,
    )
    aggregate = aggregate_quality_report([sample], expected_sample_count=1)
    aggregate["read_only_note"] = (
        "Existing evidence can prove chain structure, but cannot prove stable "
        "10-sample production quality or fresh visual consistency."
    )
    return {
        "contract_version": 1,
        "mode": "audit-existing",
        "run_id": args.run_id,
        "input_run": args.input_run,
        "samples": [sample],
        "aggregate": aggregate,
    }


def _env_int(name: str) -> int | None:
    value = os.getenv(name)
    return int(value) if value else None


if __name__ == "__main__":
    sys.exit(main())
