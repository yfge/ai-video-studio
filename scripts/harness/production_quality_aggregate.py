"""Aggregate quality reports for timeline-first provider samples."""

from __future__ import annotations

from typing import Any

from scripts.harness.production_quality_script import (
    QUALITY_PASS_THRESHOLD,
    STRUCTURED_SCORE_PASS,
)
from scripts.standard_engine import standard_reference

TIMELINE_STANDARD_ID = "STD-TIMELINE-001"


def aggregate_quality_report(
    samples: list[dict[str, Any]], *, expected_sample_count: int
) -> dict[str, Any]:
    first_attempts = [s for s in samples if int(s.get("attempt") or 1) == 1]
    finals = _latest_attempts(samples)
    first_success = sum(1 for sample in first_attempts if sample.get("passed"))
    retry_success = sum(1 for sample in finals if sample.get("passed"))
    timeline_errors = _count_hard_failure(finals, "timeline_order")
    render_errors = _count_hard_failure(finals, "render_structure")
    character_errors = _count_hard_failure(finals, "character_consistency")
    provider_billing_errors = _count_failure_category(
        finals,
        "provider_billing_or_quota_failed",
    )
    lint_scores = _numeric_values(finals, "script_lint", "overall_score")
    structured_scores = _numeric_values(finals, "structured_script_score", "average")
    checks = {
        "sample_count_matches": len(finals) == expected_sample_count,
        "first_pass_success_at_least_8_of_10": first_success >= 8,
        "retry_success_at_least_9_of_10": retry_success >= 9,
        "provider_billing_or_quota_errors_zero": provider_billing_errors == 0,
        "timeline_order_errors_zero": timeline_errors == 0,
        "render_structure_errors_zero": render_errors == 0,
        "character_hard_failures_zero": character_errors == 0,
        "script_lint_average_at_least_9": _avg(lint_scores) >= QUALITY_PASS_THRESHOLD,
        "structured_script_average_at_least_3_5": _avg(structured_scores)
        >= STRUCTURED_SCORE_PASS,
    }
    verdict = "trial_ready" if all(checks.values()) else "not_trial_ready"
    if checks["timeline_order_errors_zero"] and checks["render_structure_errors_zero"]:
        if character_errors == 0 and not all(checks.values()):
            verdict = "chain_ready_quality_not_proven"
    if provider_billing_errors:
        verdict = "provider_blocked_not_evaluable"
    return {
        **standard_reference(TIMELINE_STANDARD_ID),
        "covered_standard_ids": [TIMELINE_STANDARD_ID, "STD-SCRIPT-001"],
        "verdict": verdict,
        "checks": checks,
        "expected_sample_count": expected_sample_count,
        "sample_count": len(finals),
        "first_attempt_count": len(first_attempts),
        "first_success_count": first_success,
        "retry_adjusted_success_count": retry_success,
        "timeline_order_error_count": timeline_errors,
        "render_structure_error_count": render_errors,
        "character_hard_failure_count": character_errors,
        "provider_billing_or_quota_error_count": provider_billing_errors,
        "script_lint_average": round(_avg(lint_scores), 2),
        "structured_script_average": round(_avg(structured_scores), 2),
    }


def _latest_attempts(samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for sample in samples:
        sample_id = str(sample.get("sample_id") or len(latest) + 1)
        latest[sample_id] = sample
    return list(latest.values())


def _count_hard_failure(samples: list[dict[str, Any]], failure: str) -> int:
    return sum(1 for sample in samples if failure in sample.get("hard_failures", []))


def _count_failure_category(
    samples: list[dict[str, Any]],
    category: str,
) -> int:
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
