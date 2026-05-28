#!/usr/bin/env python3
"""Run text-only production quality validation for generated scripts."""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import requests

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from scripts.harness._common import ensure_run_dir, update_summary, write_json
from scripts.harness.production_quality_api_checks import (
    lint_script_via_api,
    score_script_via_api,
)
from scripts.harness.production_quality_live import DEFAULT_PREMISES
from scripts.harness.production_quality_script import (
    normalize_script_score,
)
from scripts.harness.provider_chain_api import generate_script, login, request_json
from scripts.harness.provider_chain_payloads import TEXT_MODEL
from scripts.harness.production_script_quality_aggregate import (
    aggregate_script_quality_report,
    repair_notes_from_sample,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--username", default=os.getenv("HARNESS_USER", "geyunfei"))
    parser.add_argument("--password", default=os.getenv("HARNESS_PASSWORD", "Gyf@845261"))
    parser.add_argument("--sample-count", type=int, default=10)
    parser.add_argument("--max-retries", type=int, default=1)
    parser.add_argument("--timeout-seconds", type=int, default=900)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_dir = ensure_run_dir(args.run_id)
    report = run_live_script_samples(args, run_dir)
    write_json(run_dir / "script_quality_report.json", report)
    update_summary(
        run_dir,
        scenario="production_script_quality_regression",
        verdict=report.get("aggregate", {}).get("verdict"),
        script_quality_report=str(run_dir / "script_quality_report.json"),
    )
    print(
        {
            "ok": report.get("aggregate", {}).get("verdict") == "script_trial_ready",
            "script_quality_report": str(run_dir / "script_quality_report.json"),
            "verdict": report.get("aggregate", {}).get("verdict"),
        }
    )
    return 0


def run_live_script_samples(args: argparse.Namespace, run_dir: Path) -> dict[str, Any]:
    samples: list[dict[str, Any]] = []
    setup_payload = {"request_chain": [], "key_artifacts": {}}
    with requests.Session() as session:
        login(session, args, setup_payload)
        _confirm_text_model(session, args, setup_payload)
        for sample_index in range(1, args.sample_count + 1):
            sample_id = f"sample-{sample_index:02d}"
            premise = DEFAULT_PREMISES[(sample_index - 1) % len(DEFAULT_PREMISES)]
            repair_notes: list[str] = []
            for attempt in range(1, args.max_retries + 2):
                sample = run_live_script_sample(
                    session,
                    args,
                    run_dir=run_dir,
                    sample_id=sample_id,
                    premise=premise,
                    attempt=attempt,
                    repair_notes=repair_notes,
                )
                samples.append(sample)
                write_json(run_dir / "script_quality_report.json", _base_report(args, samples))
                if sample.get("passed"):
                    break
                repair_notes = repair_notes_from_sample(sample)
    report = _base_report(args, samples)
    report["setup"] = setup_payload
    return report


def run_live_script_sample(
    session: requests.Session,
    args: argparse.Namespace,
    *,
    run_dir: Path,
    sample_id: str,
    premise: str,
    attempt: int,
    repair_notes: list[str],
) -> dict[str, Any]:
    started = time.monotonic()
    child_args = SimpleNamespace(
        **{
            **vars(args),
            "mode": "full-30s",
            "run_id": f"{args.run_id}-{sample_id}-attempt-{attempt}",
            "script_premise": premise,
            "script_repair_notes": repair_notes,
        }
    )
    session.headers["x-harness-run-id"] = child_args.run_id
    payload: dict[str, Any] = {"request_chain": [], "key_artifacts": {}}
    artifact = run_dir / f"{sample_id}-attempt-{attempt}-script.json"
    try:
        script = generate_script(session, child_args, payload)
        lint = lint_script_via_api(child_args, payload, f"{sample_id}-{attempt}")
        score = normalize_script_score(
            score_script_via_api(child_args, payload, f"{sample_id}-{attempt}")
        )
        structured = payload["key_artifacts"]["script"]["structured_script_score"]
        script_failures = _script_failures(lint, score, structured)
        sample = {
            "sample_id": sample_id,
            "attempt": attempt,
            "passed": not script_failures,
            "script_failures": script_failures,
            "failure_categories": [],
            "script_artifact": str(artifact),
            "script_title": script.get("title"),
            "script_premise": premise,
            "script_lint": lint,
            "script_score": score,
            "structured_script_score": structured,
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }
    except Exception as exc:  # noqa: BLE001 - report keeps the evidence
        sample = _failed_sample(sample_id, attempt, premise, artifact, exc, started)
        payload["failure"] = {"type": type(exc).__name__, "message": str(exc)}
    write_json(artifact, payload)
    return sample


def _confirm_text_model(
    session: requests.Session, args: argparse.Namespace, payload: dict[str, Any]
) -> None:
    body = request_json(
        session,
        "GET",
        f"{args.api_url.rstrip('/')}/api/v1/ai/models/available",
        params={"model_type": "text_generation"},
        chain=payload["request_chain"],
        label="models-text_generation",
        timeout=30,
    )
    models = ((body.get("data") or {}).get("models") or []) if body.get("success") else []
    if not any(
        {str(item.get("model_id", "")), str(item.get("id", ""))}
        & {f"deepseek:{TEXT_MODEL}", TEXT_MODEL}
        for item in models
    ):
        raise RuntimeError(f"required text model unavailable: {TEXT_MODEL}")


def _base_report(args: argparse.Namespace, samples: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "contract_version": 1,
        "mode": "live-text-10",
        "run_id": args.run_id,
        "api_url": args.api_url,
        "sample_count": args.sample_count,
        "samples": samples,
        "aggregate": aggregate_script_quality_report(
            samples,
            expected_sample_count=args.sample_count,
        ),
    }


def _script_failures(lint: dict, score: dict, structured: dict) -> list[str]:
    failures = []
    if lint.get("status") in {"completed", "failed"} and not lint.get("passed"):
        failures.append("script_lint")
    if score.get("status") in {"completed", "failed"} and not score.get("passed"):
        failures.append("script_score")
    if not structured.get("passed"):
        failures.append("structured_script_score")
    return failures


def _failed_sample(
    sample_id: str, attempt: int, premise: str, artifact: Path, exc: Exception, started: float
) -> dict[str, Any]:
    return {
        "sample_id": sample_id,
        "attempt": attempt,
        "passed": False,
        "script_failures": ["script_generation"],
        "failure_categories": [_script_failure_category(exc)],
        "script_artifact": str(artifact),
        "script_premise": premise,
        "error": f"{type(exc).__name__}: {exc}",
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "script_lint": {"status": "skipped", "passed": False},
        "script_score": {"status": "skipped", "passed": False},
        "structured_script_score": {"status": "skipped", "passed": False},
    }


def _script_failure_category(exc: Exception) -> str:
    evidence = f"{type(exc).__name__}: {exc}"
    if any(marker in evidence for marker in ("quota", "余额不足", "欠费", "overdue")):
        return "provider_billing_or_quota_failed"
    if "script_structured_quality_failed" in evidence:
        return "script_quality_failed"
    if "script_json_parse_failed" in evidence:
        return "script_generation_failed"
    return "unknown"


if __name__ == "__main__":
    sys.exit(main())
