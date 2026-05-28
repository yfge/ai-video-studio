import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = REPO_ROOT / "ai-pic-backend"
sys.path.append(str(REPO_ROOT))
sys.path.append(str(BACKEND_ROOT))

import pytest  # noqa: E402
from tests.scripts.provider_chain_fixtures import (  # noqa: E402
    CliffhangerManager,
    passing_script_score,
    provider_payload,
    sample,
)

from scripts.harness.production_quality_report import (  # noqa: E402
    aggregate_quality_report,
    evaluate_character_consistency,
    evaluate_provider_chain_sample,
    normalize_script_score,
)
from scripts.harness.production_quality_script import (  # noqa: E402
    lint_script_async,
    structured_script_score,
)


@pytest.mark.asyncio
async def test_script_lint_async_accepts_provider_chain_screenplay() -> None:
    payload = provider_payload()

    result = await lint_script_async(
        payload,
        ai_manager=CliffhangerManager(),
        model="deepseek-v4-flash",
        prefer_provider="deepseek",
    )

    assert result["passed"] is True
    assert "[第1场]" in result["screenplay"]
    assert not any(issue["rule_id"] == "scene_headers" for issue in result["issues"])


def test_character_gate_fails_when_shot_plan_or_task_lineage_missing() -> None:
    payload = provider_payload()
    payload["key_artifacts"]["videos"][0].pop("task_id")
    payload["key_artifacts"]["videos"][1]["timeline_shot_plan"].pop("character_anchor")

    result = evaluate_character_consistency(
        payload,
        frame_artifacts=[f"/tmp/frame-{index}.jpg" for index in range(6)],
        contact_sheet="/tmp/sheet.jpg",
    )

    assert result["passed"] is False
    assert result["clip_results"][0]["checks"]["has_seedance_task_id"] is False
    assert result["clip_results"][1]["checks"]["has_character_anchor"] is False


def test_provider_chain_sample_fails_on_timeline_order_gap() -> None:
    payload = provider_payload()
    payload["request_chain"] = [
        item
        for item in payload["request_chain"]
        if item["label"] != "timeline-shot-plan"
    ]

    sample = evaluate_provider_chain_sample(
        payload,
        provider_chain_artifact="/tmp/provider_chain.json",
        script_score=passing_script_score(),
        frame_artifacts=[f"/tmp/frame-{index}.jpg" for index in range(6)],
        contact_sheet="/tmp/sheet.jpg",
        sample_id="sample-01",
        attempt=1,
    )

    assert sample["passed"] is False
    assert "timeline_order" in sample["hard_failures"]


def test_aggregate_report_counts_retry_adjusted_success() -> None:
    failed = sample("sample-01", 1, passed=False, hard_failures=["provider_chain"])
    retry = sample("sample-01", 2, passed=True)
    successes = [
        sample(f"sample-{index:02d}", 1, passed=True) for index in range(2, 11)
    ]

    aggregate = aggregate_quality_report(
        [failed, retry, *successes],
        expected_sample_count=10,
    )

    assert aggregate["first_success_count"] == 9
    assert aggregate["retry_adjusted_success_count"] == 10
    assert aggregate["checks"]["first_pass_success_at_least_8_of_10"] is True
    assert aggregate["checks"]["retry_success_at_least_9_of_10"] is True


def test_aggregate_report_marks_provider_billing_blocker() -> None:
    samples = [
        sample(
            f"sample-{index:02d}",
            1,
            passed=False,
            hard_failures=["provider_chain"],
            failure_categories=["provider_billing_or_quota_failed"],
        )
        for index in range(1, 11)
    ]

    aggregate = aggregate_quality_report(samples, expected_sample_count=10)

    assert aggregate["verdict"] == "provider_blocked_not_evaluable"
    assert aggregate["provider_billing_or_quota_error_count"] == 10
    assert aggregate["checks"]["provider_billing_or_quota_errors_zero"] is False


def test_normalize_script_score_requires_all_dimensions_above_threshold() -> None:
    score = passing_script_score()
    score["dimension_scores"]["clip_ability"] = 3.0

    result = normalize_script_score(score)

    assert result["passed"] is False
    assert result["dimension_scores"]["clip_ability"] == 3.0


def test_structured_score_rejects_thin_provider_script() -> None:
    payload = provider_payload()
    script = json.loads(payload["key_artifacts"]["script"]["raw_content"])
    for scene in script["scenes"]:
        scene.pop("beats", None)
    payload["key_artifacts"]["script"]["raw_content"] = json.dumps(
        script, ensure_ascii=False
    )

    result = structured_script_score(payload)

    assert result["passed"] is False
    assert "scene_min_beats" in result["failed_checks"]


def test_structured_score_rejects_generic_provider_dialogue_speakers() -> None:
    payload = provider_payload()
    script = json.loads(payload["key_artifacts"]["script"]["raw_content"])
    for scene in script["scenes"]:
        scene["dialogue"][0]["speaker"] = "主角"
        for beat in scene["beats"]:
            beat["dialogue"][0]["speaker"] = "主角"
    payload["key_artifacts"]["script"]["raw_content"] = json.dumps(
        script, ensure_ascii=False
    )

    result = structured_script_score(payload)

    assert result["passed"] is False
    assert "dialogue_character_specificity" in result["failed_checks"]
    assert "scene_protagonist_presence" in result["failed_checks"]


def test_structured_score_requires_recurring_provider_scene_speaker() -> None:
    payload = provider_payload()
    script = json.loads(payload["key_artifacts"]["script"]["raw_content"])
    names = ["小蓝", "灰屏", "黑影"]
    for scene_index, scene in enumerate(script["scenes"], start=1):
        scene["dialogue"][0]["speaker"] = f"计时员{scene_index}"
        for beat, name in zip(scene["beats"], names, strict=True):
            beat["dialogue"][0]["speaker"] = f"{name}{scene_index}"
    payload["key_artifacts"]["script"]["raw_content"] = json.dumps(
        script, ensure_ascii=False
    )

    result = structured_script_score(payload)

    assert result["passed"] is False
    assert "scene_protagonist_presence" in result["failed_checks"]
    assert "dialogue_character_specificity" not in result["failed_checks"]


def test_structured_score_requires_provider_protagonist_in_screen_action() -> None:
    payload = provider_payload()
    script = json.loads(payload["key_artifacts"]["script"]["raw_content"])
    for scene in script["scenes"]:
        for beat in scene["beats"]:
            beat["visible_event"] = "控制台红灯连续闪烁"
            beat["action"] = ["屏幕弹出权限警报"]
    payload["key_artifacts"]["script"]["raw_content"] = json.dumps(
        script, ensure_ascii=False
    )

    result = structured_script_score(payload)

    assert result["passed"] is False
    assert "scene_protagonist_screen_presence" in result["failed_checks"]


def test_structured_score_rejects_generic_provider_beat_purpose() -> None:
    payload = provider_payload()
    script = json.loads(payload["key_artifacts"]["script"]["raw_content"])
    for scene in script["scenes"]:
        for beat in scene["beats"]:
            beat["dramatic_purpose"] = "推进剧情"
    payload["key_artifacts"]["script"]["raw_content"] = json.dumps(
        script, ensure_ascii=False
    )

    result = structured_script_score(payload)

    assert result["passed"] is False
    assert "beat_dramatic_purpose_specificity" in result["failed_checks"]


def test_structured_score_requires_provider_beat_durations() -> None:
    payload = provider_payload()
    script = json.loads(payload["key_artifacts"]["script"]["raw_content"])
    for scene in script["scenes"]:
        for beat in scene["beats"]:
            beat.pop("duration_seconds", None)
    payload["key_artifacts"]["script"]["raw_content"] = json.dumps(
        script, ensure_ascii=False
    )

    result = structured_script_score(payload)

    assert result["passed"] is False
    assert "beat_duration_required" in result["failed_checks"]


def test_structured_score_rejects_provider_scene_duration_mismatch() -> None:
    payload = provider_payload()
    script = json.loads(payload["key_artifacts"]["script"]["raw_content"])
    for scene in script["scenes"]:
        for beat in scene["beats"]:
            beat["duration_seconds"] = 2
    payload["key_artifacts"]["script"]["raw_content"] = json.dumps(
        script, ensure_ascii=False
    )

    result = structured_script_score(payload)

    assert result["passed"] is False
    assert "scene_duration_alignment" in result["failed_checks"]


def test_structured_score_rejects_internal_state_provider_beats() -> None:
    payload = provider_payload()
    script = json.loads(payload["key_artifacts"]["script"]["raw_content"])
    scene = script["scenes"][0]
    scene["beats"][0]["visible_event"] = "小蓝意识到真相正在改变命运。"
    scene["beats"][0]["action"] = ["小蓝内心感到崩溃。"]
    payload["key_artifacts"]["script"]["raw_content"] = json.dumps(
        script, ensure_ascii=False
    )

    result = structured_script_score(payload)

    assert result["passed"] is False
    assert "beat_visible_event_specificity" in result["failed_checks"]
    assert "beat_action_specificity" in result["failed_checks"]


def test_structured_score_rejects_filler_provider_dialogue() -> None:
    payload = provider_payload()
    script = json.loads(payload["key_artifacts"]["script"]["raw_content"])
    for scene in script["scenes"]:
        scene["dialogue"][0]["line"] = "好的"
        for beat in scene["beats"]:
            beat["dialogue"][0]["line"] = "好的"
    payload["key_artifacts"]["script"]["raw_content"] = json.dumps(
        script, ensure_ascii=False
    )

    result = structured_script_score(payload)

    assert result["passed"] is False
    assert "dialogue_substance" in result["failed_checks"]
