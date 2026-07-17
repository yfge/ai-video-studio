from __future__ import annotations

import pytest
from app.services.script.production_pipeline import (
    render_production_requirements,
    run_production_script_generation,
)


def _scoring(
    verdict: str,
    overall: float,
    *,
    dimensions: dict[str, float] | None = None,
    asset_count: int = 1,
) -> dict:
    dimension_scores = dimensions or {
        "conflict_intensity": overall,
        "character_recognizability": overall,
        "cultural_fit": overall,
        "clip_ability": overall,
        "logic_coherence": overall,
    }
    return {
        "script_score": {
            "overall_score": overall,
            "verdict": verdict,
            "dimension_scores": dimension_scores,
            "rewrite_guidance": [],
        },
        "traffic_sheet": {"assets": []},
        "asset_tags": {"asset_count": asset_count, "hook_types": ["reveal"]},
    }


@pytest.mark.unit
@pytest.mark.asyncio
async def test_production_generation_derives_guidance_from_strict_score_gaps():
    generated_requirements: list[str] = []
    scores = [
        _scoring(
            "review",
            4.2,
            dimensions={
                "conflict_intensity": 4.5,
                "character_recognizability": 4.0,
                "cultural_fit": 4.5,
                "clip_ability": 4.0,
                "logic_coherence": 4.0,
            },
            asset_count=0,
        ),
        _scoring("pass", 4.6, asset_count=3),
    ]

    async def generate_attempt(attempt_no: int, requirements: str) -> dict:
        generated_requirements.append(requirements)
        return {
            "attempt": attempt_no,
            "result": {"generation_method": f"fake-{attempt_no}"},
            "ai_content": {"content": f"draft {attempt_no}"},
            "script_content": f"draft {attempt_no}",
            "scenes": [],
            "dialogues": [],
            "stage_directions": [],
        }

    async def score_attempt(_generated: dict) -> dict:
        return scores.pop(0)

    result = await run_production_script_generation(
        story={"title": "T"},
        episode={"summary": "S"},
        marketing_overrides={},
        base_additional_requirements=None,
        generate_attempt=generate_attempt,
        score_attempt=score_attempt,
    )

    assert result.selected_attempt == 2
    assert "整体 ScriptScore 必须提升到 4.5+" in generated_requirements[1]
    assert "character_recognizability=4.0" in generated_requirements[1]
    assert "clip_ability=4.0" in generated_requirements[1]
    assert "logic_coherence=4.0" in generated_requirements[1]
    assert "按实际成片时长" in generated_requirements[1]


@pytest.mark.unit
def test_render_production_requirements_expands_commercial_rewrite_contract():
    requirements = render_production_requirements(
        base_additional_requirements=None,
        hook_schedule={"opening_hook": "客户拍桌质疑数据"},
        rewrite_guidance=["角色辨识度不足", "逻辑一致性有漏洞"],
        attempt_no=2,
    )

    assert "商业评分硬交付清单" in requirements
    assert "overall_score >= 4.5" in requirements
    assert "每项 >= 4.2" in requirements
    assert "按实际成片总时长" in requirements
    assert "不得用评分样板替换用户题材" in requirements
    assert "不得为了凑评分擅自新增无关人物" in requirements
    assert "客户张总给出60秒撤单倒计时" not in requirements
    assert "改完给你20万，不做就裁你" not in requirements
    assert "返修落地校验" in requirements
    assert "针对「角色辨识度不足」" in requirements
    assert "visible_event" in requirements
    assert "action_line" in requirements
