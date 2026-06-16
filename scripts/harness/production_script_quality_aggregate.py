"""Aggregate and feedback helpers for script-only quality runs."""

from __future__ import annotations

from typing import Any

from scripts.harness.production_quality_script import (
    QUALITY_PASS_THRESHOLD,
    SCRIPT_SCORE_DIMENSION_PASS,
    SCRIPT_SCORE_PASS,
    STRUCTURED_SCORE_PASS,
)
from scripts.standard_engine import standard_reference

SCRIPT_STANDARD_ID = "STD-SCRIPT-001"


def aggregate_script_quality_report(
    samples: list[dict[str, Any]], *, expected_sample_count: int
) -> dict[str, Any]:
    first_attempts = [s for s in samples if int(s.get("attempt") or 1) == 1]
    finals = _latest_attempts(samples)
    first_success = sum(1 for sample in first_attempts if sample.get("passed"))
    retry_success = sum(1 for sample in finals if sample.get("passed"))
    provider_errors = _count_failure_category(finals, "provider_billing_or_quota_failed")
    lint_scores = _numeric_values(finals, "script_lint", "overall_score")
    script_scores = _numeric_values(finals, "script_score", "overall_score")
    structured_scores = _numeric_values(finals, "structured_script_score", "average")
    checks = {
        "sample_count_matches": len(finals) == expected_sample_count,
        "first_pass_success_at_least_8_of_10": first_success >= 8,
        "retry_success_at_least_9_of_10": retry_success >= 9,
        "provider_billing_or_quota_errors_zero": provider_errors == 0,
        "script_lint_average_at_least_9": _avg(lint_scores) >= QUALITY_PASS_THRESHOLD,
        "script_score_average_at_least_4": _avg(script_scores) >= SCRIPT_SCORE_PASS,
        "structured_script_average_at_least_3_5": _avg(structured_scores)
        >= STRUCTURED_SCORE_PASS,
    }
    verdict = "script_trial_ready" if all(checks.values()) else "script_quality_not_proven"
    if provider_errors:
        verdict = "provider_blocked_not_evaluable"
    return {
        **standard_reference(SCRIPT_STANDARD_ID),
        "verdict": verdict,
        "checks": checks,
        "expected_sample_count": expected_sample_count,
        "sample_count": len(finals),
        "first_attempt_count": len(first_attempts),
        "first_success_count": first_success,
        "retry_adjusted_success_count": retry_success,
        "provider_billing_or_quota_error_count": provider_errors,
        "script_lint_average": round(_avg(lint_scores), 2),
        "script_score_average": round(_avg(script_scores), 2),
        "structured_script_average": round(_avg(structured_scores), 2),
    }


def repair_notes_from_sample(sample: dict[str, Any]) -> list[str]:
    notes: list[str] = []
    score = sample.get("script_score") if isinstance(sample.get("script_score"), dict) else {}
    notes.extend(_low_dimension_notes(score))
    notes.extend(str(item) for item in score.get("risks") or [] if item)
    notes.extend(str(item) for item in score.get("rewrite_guidance") or [] if item)
    structured = sample.get("structured_script_score")
    if isinstance(structured, dict):
        failed = ", ".join(str(item) for item in structured.get("failed_checks") or [])
        if failed:
            notes.append(f"structured failed checks: {failed}")
    lint = sample.get("script_lint")
    if isinstance(lint, dict):
        for issue in lint.get("issues") or []:
            if isinstance(issue, dict) and issue.get("message"):
                notes.append(str(issue["message"]))
    return notes[:8]


def _low_dimension_notes(score: dict[str, Any]) -> list[str]:
    dimensions = score.get("dimension_scores")
    if not isinstance(dimensions, dict):
        return []
    notes: list[str] = []
    for name, value in dimensions.items():
        number = _maybe_float(value)
        if number is not None and number < SCRIPT_SCORE_DIMENSION_PASS:
            notes.append(f"low dimension {name}={number:g}")
    return notes


def _latest_attempts(samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for sample in samples:
        sample_id = str(sample.get("sample_id") or len(latest) + 1)
        latest[sample_id] = sample
    return list(latest.values())


def _count_failure_category(samples: list[dict[str, Any]], category: str) -> int:
    return sum(1 for sample in samples if category in sample.get("failure_categories", []))


def _numeric_values(samples: list[dict[str, Any]], group: str, key: str) -> list[float]:
    values = []
    for sample in samples:
        value = _maybe_float(sample.get(group, {}).get(key))
        if value is not None:
            values.append(value)
    return values


def _maybe_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0
