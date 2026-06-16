import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = REPO_ROOT / "ai-pic-backend"
sys.path.append(str(REPO_ROOT))
sys.path.append(str(BACKEND_ROOT))

from tests.scripts.provider_chain_fixtures import (  # noqa: E402
    passing_script_score,
    provider_payload,
    sample,
)

from scripts.harness.production_quality_report import (  # noqa: E402
    aggregate_quality_report,
    evaluate_character_consistency,
    evaluate_provider_chain_sample,
)
from scripts.harness.production_quality_script import (  # noqa: E402
    structured_script_score,
)


def test_timeline_provider_chain_outputs_standard_metadata() -> None:
    payload = provider_payload()
    payload["request_chain"] = [
        item
        for item in payload["request_chain"]
        if item["label"] != "timeline-shot-plan"
    ]

    result = evaluate_provider_chain_sample(
        payload,
        provider_chain_artifact="/tmp/provider_chain.json",
        script_score=passing_script_score(),
        frame_artifacts=[f"/tmp/frame-{index}.jpg" for index in range(6)],
        contact_sheet="/tmp/sheet.jpg",
        sample_id="sample-01",
        attempt=1,
    )

    assert result["standard_id"] == "STD-TIMELINE-001"
    assert result["standard_doc"] == "docs/standards/STD-TIMELINE-001.md"
    assert result["timeline_order"]["standard_id"] == "STD-TIMELINE-001"
    assert result["render_structure"]["standard_id"] == "STD-TIMELINE-001"


def test_timeline_character_gate_outputs_standard_metadata() -> None:
    payload = provider_payload()
    payload["key_artifacts"]["videos"][0].pop("task_id")

    result = evaluate_character_consistency(
        payload,
        frame_artifacts=[f"/tmp/frame-{index}.jpg" for index in range(6)],
        contact_sheet="/tmp/sheet.jpg",
    )

    assert result["standard_id"] == "STD-TIMELINE-001"
    assert result["standard_doc"] == "docs/standards/STD-TIMELINE-001.md"


def test_quality_aggregate_outputs_timeline_and_script_standards() -> None:
    failed = sample("sample-01", 1, passed=False, hard_failures=["provider_chain"])
    retry = sample("sample-01", 2, passed=True)
    successes = [
        sample(f"sample-{index:02d}", 1, passed=True) for index in range(2, 11)
    ]

    aggregate = aggregate_quality_report(
        [failed, retry, *successes],
        expected_sample_count=10,
    )

    assert aggregate["standard_id"] == "STD-TIMELINE-001"
    assert aggregate["covered_standard_ids"] == [
        "STD-TIMELINE-001",
        "STD-SCRIPT-001",
    ]


def test_structured_script_score_outputs_script_standard_metadata() -> None:
    result = structured_script_score(provider_payload())

    assert result["standard_id"] == "STD-SCRIPT-001"
    assert result["standard_doc"] == "docs/standards/STD-SCRIPT-001.md"
