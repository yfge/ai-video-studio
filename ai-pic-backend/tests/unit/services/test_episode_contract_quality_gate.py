from __future__ import annotations

import pytest
from app.services.narrative_quality_gate import evaluate_episode_quality_gate


def _episode() -> dict:
    return {
        "episode_number": 1,
        "title": "第1集",
        "summary": "林雪发现账本里的秘密，危机升级。",
        "plot_points": [{"description": "林雪夺到账本，陈默追上来。"}],
        "conflicts": [{"description": "林雪和陈默争夺账本", "intensity": "high"}],
        "scene_count": 1,
        "scenes": [
            {
                "scene_number": 1,
                "slug_line": "Scene 1",
                "summary": "林雪夺到账本。",
            }
        ],
    }


@pytest.mark.unit
def test_episode_gate_requires_structured_contract_in_production() -> None:
    gate = evaluate_episode_quality_gate(
        episodes=[_episode()],
        story={"characters": [{"name": "林雪"}]},
        episode_count=1,
        require_episode_contract=True,
    )

    assert gate["passed"] is False
    assert any(
        issue["id"] == "structured_episode_contract_required"
        for issue in gate["blocking_issues"]
    )


@pytest.mark.unit
def test_episode_gate_accepts_structured_contract_when_required() -> None:
    episode = _episode()
    episode["payoff"] = "林雪当众拿到账本，逼陈默交出钥匙。"
    episode["cliffhanger"] = "账本最后一页露出林雪父亲的签名。"
    episode["structured_episode_contract"] = {
        "episode_goal": "林雪夺到账本",
        "ignition_0_3s": "林雪撞开门，账本被陈默塞进保险箱。",
        "first_30s_reason": "观众立刻知道账本决定林雪能否翻案。",
        "midpoint_jolt": "陈默亮出第二把钥匙，反咬林雪偷窃。",
        "payoff": "林雪用手机录音反击，拿到账本。",
        "final_button_cliffhanger": "账本最后一页出现父亲签名。",
        "visual_anchor": "手机录音界面特写、林雪攥紧账本的手。",
        "information_delta": "观众得知父亲可能参与旧案。",
        "dialogue_functions": ["reveal", "counterattack", "payoff"],
    }

    gate = evaluate_episode_quality_gate(
        episodes=[episode],
        story={"characters": [{"name": "林雪"}]},
        episode_count=1,
        require_episode_contract=True,
    )

    blocking_ids = {issue["id"] for issue in gate["blocking_issues"]}
    assert "structured_episode_contract_required" not in blocking_ids
