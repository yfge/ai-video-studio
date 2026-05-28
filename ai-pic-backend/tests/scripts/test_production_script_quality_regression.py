import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(REPO_ROOT))

from scripts.harness.production_script_quality_regression import (  # noqa: E402
    _failed_sample,
    aggregate_script_quality_report,
    repair_notes_from_sample,
)


def test_script_quality_aggregate_requires_10_sample_stability() -> None:
    samples = [
        _script_sample(f"sample-{index:02d}", passed=True) for index in range(1, 10)
    ]

    report = aggregate_script_quality_report(samples, expected_sample_count=10)

    assert report["verdict"] == "script_quality_not_proven"
    assert report["checks"]["sample_count_matches"] is False
    assert report["retry_adjusted_success_count"] == 9


def test_script_quality_aggregate_marks_trial_ready() -> None:
    samples = [
        _script_sample(f"sample-{index:02d}", passed=True) for index in range(1, 11)
    ]

    report = aggregate_script_quality_report(samples, expected_sample_count=10)

    assert report["verdict"] == "script_trial_ready"
    assert all(report["checks"].values())
    assert report["script_lint_average"] == 9.2
    assert report["script_score_average"] == 4.2
    assert report["structured_script_average"] == 3.8


def test_script_quality_aggregate_counts_retry_adjusted_success() -> None:
    samples = [_script_sample("sample-01", passed=False, attempt=1)]
    samples.append(_script_sample("sample-01", passed=True, attempt=2))
    samples.extend(
        _script_sample(f"sample-{index:02d}", passed=True) for index in range(2, 11)
    )

    report = aggregate_script_quality_report(samples, expected_sample_count=10)

    assert report["first_success_count"] == 9
    assert report["retry_adjusted_success_count"] == 10
    assert report["checks"]["first_pass_success_at_least_8_of_10"] is True
    assert report["checks"]["retry_success_at_least_9_of_10"] is True


def test_script_quality_aggregate_marks_provider_blocker() -> None:
    samples = [
        _script_sample(
            f"sample-{index:02d}",
            passed=False,
            failure_categories=["provider_billing_or_quota_failed"],
        )
        for index in range(1, 11)
    ]

    report = aggregate_script_quality_report(samples, expected_sample_count=10)

    assert report["verdict"] == "provider_blocked_not_evaluable"
    assert report["provider_billing_or_quota_error_count"] == 10


def test_repair_notes_include_script_score_and_structured_feedback() -> None:
    sample = {
        "script_failures": ["script_score", "structured_script_score"],
        "script_score": {
            "dimension_scores": {
                "logic_coherence": 3.2,
                "character_recognizability": 3.4,
                "clip_ability": 4.2,
            },
            "risks": ["角色辨识度不足：台词可互换"],
            "rewrite_guidance": ["给主角固定口头禅，并补前置线索"],
        },
        "structured_script_score": {
            "failed_checks": ["opening_hook_substance", "scene_conflict_opposition"]
        },
    }

    notes = repair_notes_from_sample(sample)
    joined = "\n".join(notes)

    assert "角色辨识度不足" in joined
    assert "给主角固定口头禅" in joined
    assert "opening_hook_substance" in joined
    assert "scene_conflict_opposition" in joined
    assert "low dimension logic_coherence=3.2" in joined
    assert "low dimension character_recognizability=3.4" in joined
    assert "clip_ability=4.2" not in joined


def test_failed_sample_preserves_structured_score_for_repair_notes() -> None:
    sample = _failed_sample(
        "sample-01",
        1,
        "premise",
        Path("sample.json"),
        ValueError("script_structured_quality_failed: opening_hook_substance"),
        0.0,
        payload={
            "key_artifacts": {
                "script": {
                    "structured_script_score": {
                        "passed": False,
                        "average": 3.2,
                        "failed_checks": ["opening_hook_substance"],
                    }
                }
            }
        },
    )

    assert sample["script_failures"] == ["structured_script_score"]
    assert sample["structured_script_score"]["failed_checks"] == [
        "opening_hook_substance"
    ]
    assert "opening_hook_substance" in "\n".join(repair_notes_from_sample(sample))


def _script_sample(
    sample_id: str,
    *,
    passed: bool,
    attempt: int = 1,
    failure_categories: list[str] | None = None,
) -> dict:
    return {
        "sample_id": sample_id,
        "attempt": attempt,
        "passed": passed,
        "failure_categories": failure_categories or [],
        "script_lint": {"overall_score": 9.2, "passed": passed},
        "script_score": {"overall_score": 4.2, "passed": passed},
        "structured_script_score": {"average": 3.8, "passed": passed},
    }
