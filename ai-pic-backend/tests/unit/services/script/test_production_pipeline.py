from __future__ import annotations

import pytest

from app.services.script.production_pipeline import (
    annotate_storyboard_frames_with_hooks,
    build_hook_schedule,
    run_production_script_generation,
    score_passes,
)


def _scoring(verdict: str, overall: float, guidance: list[str] | None = None) -> dict:
    return {
        "script_score": {
            "overall_score": overall,
            "verdict": verdict,
            "dimension_scores": {
                "conflict_intensity": overall,
                "character_recognizability": overall,
                "cultural_fit": overall,
                "clip_ability": overall,
                "logic_coherence": overall,
            },
            "rewrite_guidance": guidance or [],
        },
        "traffic_sheet": {
            "assets": [
                {
                    "duration_seconds": 15,
                    "hook_type": "reveal",
                    "key_line": "她把证据举到镜头前",
                    "visual_hook": "主角当众举证",
                    "cliff_or_cta": "继续看她如何反击",
                }
            ]
        },
        "asset_tags": {"asset_count": 1, "hook_types": ["reveal"]},
    }


@pytest.mark.unit
def test_build_hook_schedule_uses_marketing_and_episode_beats():
    schedule = build_hook_schedule(
        {"title": "T", "main_conflict": "身份被抢"},
        {
            "summary": "女主被当众羞辱",
            "plot_points": [{"description": "女主拿出录音", "timing": "中段"}],
        },
        {
            "hook_plan": {
                "opening_hook": "婚礼现场背叛",
                "payoff_plan": "女主播放证据反击",
            },
            "cliffhanger_plan": ["反派亮出亲子鉴定"],
            "ad_snippets": [
                {
                    "duration_seconds": 15,
                    "hook": "她不是替身",
                    "visual_summary": "女主撕掉假合同",
                }
            ],
        },
    )

    assert schedule["opening_hook"] == "婚礼现场背叛"
    assert schedule["payoff"] == "女主播放证据反击"
    assert schedule["cliffhanger"] == "反派亮出亲子鉴定"
    assert schedule["conflict_ladder"][0]["description"] == "女主拿出录音"
    assert schedule["ad_candidate_beats"][0]["hook"] == "她不是替身"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_production_generation_skips_rewrite_when_score_passes():
    generated_requirements: list[str] = []

    async def generate_attempt(attempt_no: int, requirements: str) -> dict:
        generated_requirements.append(requirements)
        return {
            "attempt": attempt_no,
            "result": {"generation_method": "fake"},
            "ai_content": {"content": "ok"},
            "script_content": "ok",
            "scenes": [],
            "dialogues": [],
            "stage_directions": [],
        }

    async def score_attempt(_generated: dict) -> dict:
        return _scoring("pass", 4.3)

    result = await run_production_script_generation(
        story={"title": "T"},
        episode={"summary": "S"},
        marketing_overrides={},
        base_additional_requirements=None,
        generate_attempt=generate_attempt,
        score_attempt=score_attempt,
    )

    assert len(result.attempts) == 1
    assert result.selected_attempt == 1
    assert result.review_required is False
    assert "hook_schedule" in generated_requirements[0]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_production_generation_rewrites_and_selects_pass():
    generated_requirements: list[str] = []
    scores = [_scoring("rewrite", 2.5, ["补强开场冲突"]), _scoring("pass", 4.2)]

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
        base_additional_requirements="保持低成本",
        generate_attempt=generate_attempt,
        score_attempt=score_attempt,
    )

    assert len(result.attempts) == 2
    assert result.selected_attempt == 2
    assert result.review_required is False
    assert "补强开场冲突" in generated_requirements[1]
    assert result.metadata()["selected_attempt"] == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_production_generation_uses_max_two_repair_attempts():
    calls: list[int] = []
    scores = [
        _scoring("rewrite", 2.1, ["重写前3秒钩子"]),
        _scoring("rewrite", 3.2, ["压缩中段解释"]),
        _scoring("pass", 3.8, ["仍需人工复核"]),
    ]

    async def generate_attempt(attempt_no: int, _requirements: str) -> dict:
        calls.append(attempt_no)
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

    assert calls == [1, 2, 3]
    assert len(result.attempts) == 3
    assert result.review_required is True
    assert result.selected_attempt == 3


@pytest.mark.unit
def test_score_pass_requires_thresholds_even_when_verdict_is_pass():
    scoring = _scoring("pass", 3.9)

    assert score_passes(scoring) is False


@pytest.mark.unit
def test_annotate_storyboard_frames_with_hooks_uses_traffic_sheet():
    frames = [
        {"description": "女主冲进会议室", "beat_type": "action"},
        {"description": "女主举起证据完成反击", "beat_type": "dialogue"},
        {"description": "门外突然出现黑衣人", "beat_type": "action"},
    ]

    changed = annotate_storyboard_frames_with_hooks(
        frames,
        hook_schedule={"opening_hook": "冲突开场"},
        scoring=_scoring("pass", 4.5),
    )

    assert changed >= 2
    assert frames[0]["hook_tag"] == "opening_hook"
    assert frames[0]["ad_snippet"]["hook"] == "她把证据举到镜头前"
    assert frames[1]["hook_tag"] == "payoff"
    assert frames[2]["hook_tag"] == "cliffhanger"
