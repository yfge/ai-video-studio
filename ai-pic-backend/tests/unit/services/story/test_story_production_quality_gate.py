from __future__ import annotations

import pytest
from app.services.story_quality_gate import evaluate_story_quality_gate


def _strong_story() -> dict:
    return {
        "premise": "林雪在公司发布会突然发现父亲旧案证据被公开，必须当场反击。",
        "synopsis": (
            "突然，林雪在发布会现场发现旧案证据被公开，危机和冲突立刻爆发。"
            "她顶住压力反查证据，紧张对抗不断升级，中段揭示陈默才是真正操盘者。"
            "最终高潮对决中真相曝光，林雪完成反击并收束阶段目标。"
        ),
        "main_conflict": "林雪必须在公开羞辱和旧案陷害中找出真相。",
        "resolution": "林雪夺回关键证据，逼陈默暴露下一层黑手。",
        "plot_structure": {
            "act1": "突然公开旧案证据，林雪被迫当场反击。",
            "act2": "危机升级，林雪和陈默围绕账本紧张对抗。",
            "act3": "高潮揭示真相，林雪解决危机并完成逆袭。",
        },
        "hook_plan": {
            "opening_hook": "突然，发布会大屏播放林雪父亲旧案视频。",
            "escalation_plan": "每三集推进一个证据目标。",
            "payoff_plan": "林雪用录音反击陈默。",
        },
        "cliffhanger_plan": ["账本最后一页露出父亲签名"],
        "ad_snippets": [
            {
                "duration_seconds": 15,
                "hook": "旧案证据公开",
                "visual_summary": "大屏视频和林雪握紧手机的手",
                "call_to_action": "看她如何反击",
            }
        ],
    }


@pytest.mark.unit
def test_story_gate_requires_structured_contract_in_production() -> None:
    gate = evaluate_story_quality_gate(
        story=_strong_story(),
        require_story_contract=True,
    )

    assert gate["passed"] is False
    assert any(
        issue["id"] == "structured_story_contract_required"
        for issue in gate["blocking_issues"]
    )


@pytest.mark.unit
def test_story_gate_accepts_structured_contract_when_required() -> None:
    story = _strong_story()
    story["structured_story_contract"] = {
        "target_audience": "都市复仇女性用户",
        "core_emotional_pain": "父亲蒙冤、尊严被公开碾压",
        "big_expectation": "林雪查清旧案并夺回家族公司",
        "small_expectation_ladder": [
            "前三集拿到发布会录音",
            "第十集逼陈默交出账本",
        ],
        "protagonist_goal": "三天内拿到账本",
        "structural_conflict": "林雪必须借陈默的资源查陈默的罪证",
        "information_gap": "观众知道账本在保险箱，林雪只知道陈默撒谎",
        "first_three_episode_spine": "身份、旧案、核心冲突在前三集全部立住",
        "stage_highs": ["发布会反击", "账本争夺", "董事会翻盘"],
        "shootability": "办公室、发布会厅、走廊三类低成本场景",
        "compliance_risks": [],
        "traffic_hooks": ["大屏旧案视频", "手机录音反击"],
    }

    gate = evaluate_story_quality_gate(
        story=story,
        require_story_contract=True,
    )

    blocking_ids = {issue["id"] for issue in gate["blocking_issues"]}
    assert "structured_story_contract_required" not in blocking_ids
