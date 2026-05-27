import json
import sys
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(REPO_ROOT))

import pytest

from scripts.harness.production_quality_script import lint_script_async  # noqa: E402
from scripts.harness.production_quality_report import (  # noqa: E402
    aggregate_quality_report,
    evaluate_character_consistency,
    evaluate_provider_chain_sample,
    normalize_script_score,
)
from scripts.harness.provider_chain_payloads import build_script_prompt  # noqa: E402


def test_build_script_prompt_accepts_optional_premise() -> None:
    prompt = build_script_prompt("full-30s", "奖金清零，机器人必须找出真相")

    assert "奖金清零" in prompt
    assert "Create exactly 2 scene" in prompt
    assert "<= 15 visible" in prompt
    assert "one stable protagonist" in prompt


@pytest.mark.asyncio
async def test_script_lint_async_accepts_provider_chain_screenplay() -> None:
    payload = _provider_payload()

    result = await lint_script_async(
        payload,
        ai_manager=_CliffhangerManager(),
        model="deepseek-v4-flash",
        prefer_provider="deepseek",
    )

    assert result["passed"] is True
    assert "[第1场]" in result["screenplay"]
    assert not any(issue["rule_id"] == "scene_headers" for issue in result["issues"])


def test_character_gate_fails_when_shot_plan_or_task_lineage_missing() -> None:
    payload = _provider_payload()
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
    payload = _provider_payload()
    payload["request_chain"] = [
        item
        for item in payload["request_chain"]
        if item["label"] != "timeline-shot-plan"
    ]

    sample = evaluate_provider_chain_sample(
        payload,
        provider_chain_artifact="/tmp/provider_chain.json",
        script_score=_passing_script_score(),
        frame_artifacts=[f"/tmp/frame-{index}.jpg" for index in range(6)],
        contact_sheet="/tmp/sheet.jpg",
        sample_id="sample-01",
        attempt=1,
    )

    assert sample["passed"] is False
    assert "timeline_order" in sample["hard_failures"]


def test_aggregate_report_counts_retry_adjusted_success() -> None:
    failed = _sample("sample-01", 1, passed=False, hard_failures=["provider_chain"])
    retry = _sample("sample-01", 2, passed=True)
    successes = [_sample(f"sample-{index:02d}", 1, passed=True) for index in range(2, 11)]

    aggregate = aggregate_quality_report(
        [failed, retry, *successes],
        expected_sample_count=10,
    )

    assert aggregate["first_success_count"] == 9
    assert aggregate["retry_adjusted_success_count"] == 10
    assert aggregate["checks"]["first_pass_success_at_least_8_of_10"] is True
    assert aggregate["checks"]["retry_success_at_least_9_of_10"] is True


def test_normalize_script_score_requires_all_dimensions_above_threshold() -> None:
    score = _passing_script_score()
    score["dimension_scores"]["clip_ability"] = 3.0

    result = normalize_script_score(score)

    assert result["passed"] is False
    assert result["dimension_scores"]["clip_ability"] == 3.0


def _provider_payload() -> dict:
    script = {
        "title": "奖金清零",
        "logline": "机器人发现奖金倒计时清零，最后一秒反转真相。",
        "characters": [
            {
                "name": "小蓝",
                "role": "主角",
                "appearance_prompt": "蓝色卡通机器人，橙色围巾",
                "consistency_anchor": "blue cartoon robot, orange scarf, LED eyes",
            }
        ],
        "scenes": [
            {
                "scene_id": "s1",
                "duration_seconds": 15,
                "plot": "小蓝发现奖金被清零，警报响起。",
                "dialogue": [{"speaker": "小蓝", "line": "谁动了时间轴"}],
                "image_prompt": "cartoon robot in studio",
                "video_prompt": "blue robot sees countdown alarm",
            },
            {
                "scene_id": "s2",
                "duration_seconds": 15,
                "plot": "小蓝发现真相，最后一秒反转。",
                "dialogue": [{"speaker": "小蓝", "line": "原来证据在这里"}],
                "image_prompt": "cartoon robot finds proof",
                "video_prompt": "blue robot reveals proof",
            },
        ],
    }
    return {
        "ok": True,
        "request_chain": [
            {"label": "deepseek-script", "duration_seconds": 1.0},
            {"label": "timeline-create", "duration_seconds": 0.1},
            {"label": "timeline-shot-plan", "duration_seconds": 1.0},
            {"label": "openai-character-image", "duration_seconds": 2.0},
            {"label": "seedance-video-1", "duration_seconds": 10.0},
            {"label": "seedance-video-2", "duration_seconds": 10.0},
            {"label": "timeline-assets-update", "duration_seconds": 0.1},
            {"label": "timeline-render-queue", "duration_seconds": 0.1},
        ],
        "key_artifacts": {
            "script": {"raw_content": json.dumps(script, ensure_ascii=False)},
            "image": {"oss_url": "https://example.com/robot.png"},
            "timeline_seed": {"id": 23, "version": 1},
            "timeline_shot_plan": {"id": 23, "seed_version": 1, "version": 2},
            "timeline": {"id": 23, "version": 3},
            "render_job": {
                "output_url": "https://example.com/render.mp4",
                "status": "succeeded",
            },
            "render_media_probe": {
                "ok": True,
                "expected_duration_seconds": 30,
                "format_duration_seconds": 30.1,
                "video_duration_seconds": 30.1,
                "audio_duration_seconds": 30.0,
                "checks": {
                    "has_video_stream": True,
                    "has_audio_stream": True,
                    "format_duration_matches_timeline": True,
                    "video_duration_matches_timeline": True,
                    "audio_duration_matches_timeline": True,
                    "scene_frames_extracted": True,
                },
            },
            "videos": [
                _video("video_s1_provider_chain_1_001", 1),
                _video("video_s2_provider_chain_2_002", 2),
            ],
        },
    }


def _video(clip_id: str, ordinal: int) -> dict:
    return {
        "ordinal": ordinal,
        "clip_id": clip_id,
        "duration_seconds": 15,
        "video_url": f"https://example.com/video-{ordinal}.mp4",
        "image_url": "https://example.com/robot.png",
        "provider": "volcengine",
        "model": "doubao-seedance-2-0-260128",
        "task_id": f"task-{ordinal}",
        "timeline_shot_plan": {
            "character_anchor": "blue cartoon robot, orange scarf, LED eyes",
            "dialogue_source": "小蓝: 证据在这里",
            "video_prompt": "blue robot acts with clear story beat",
        },
    }


def _passing_script_score() -> dict:
    return {
        "provider": "deepseek",
        "model": "deepseek-v4-flash",
        "verdict": "pass",
        "overall_score": 4.2,
        "dimension_scores": {
            "conflict_intensity": 4.0,
            "character_recognizability": 4.2,
            "cultural_fit": 4.1,
            "clip_ability": 4.0,
            "logic_coherence": 4.3,
        },
    }


class _CliffhangerManager:
    async def generate_text(self, **kwargs):
        return SimpleNamespace(
            success=True,
            provider="deepseek",
            model=kwargs.get("model") or "deepseek-v4-flash",
            data={
                "passed": True,
                "score": 1.0,
                "reason": "结尾继续抛问题",
                "evidence": "最后一句留下证据疑问",
                "suggestion": "",
            },
        )


def _sample(
    sample_id: str,
    attempt: int,
    *,
    passed: bool,
    hard_failures: list[str] | None = None,
) -> dict:
    return {
        "sample_id": sample_id,
        "attempt": attempt,
        "passed": passed,
        "hard_failures": hard_failures or [],
        "script_lint": {"overall_score": 9.2},
        "structured_script_score": {"average": 3.8},
    }
