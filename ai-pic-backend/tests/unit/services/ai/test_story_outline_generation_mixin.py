from __future__ import annotations

import logging
from typing import Any

import app.services.ai.story_outline as story_outline_module
import pytest
from app.services.ai.story_outline import StoryOutlineMixin


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_story_outline_direct_production_prompt_requires_contract(
    monkeypatch,
) -> None:
    captured: dict[str, Any] = {}

    async def _fake_generate_with_repair(**kwargs: Any) -> dict[str, Any]:
        captured["base_prompt"] = kwargs["base_prompt"]
        return {
            "content": '{"premise":"p"}',
            "normalized": {
                "premise": "Hero在发布会发现证据被抢，必须当场反击。",
                "synopsis": "Hero围绕证据抢夺和公开羞辱反击，前三集立住核心冲突。",
                "structured_story_contract": {
                    "target_audience": "都市复仇用户",
                    "core_emotional_pain": "尊严被公开碾压",
                    "big_expectation": "Hero夺回证据并查出黑手",
                    "small_expectation_ladder": ["前三集拿录音", "第十集逼出账本"],
                    "protagonist_goal": "抢回发布会陷害证据",
                    "structural_conflict": "Hero必须借对手资源反查对手",
                    "information_gap": "观众知道录音存在，对手不知道已入镜",
                    "first_three_episode_spine": "身份、证据、黑手前三集立住",
                    "stage_highs": ["发布会反击", "董事会翻盘"],
                    "shootability": "发布会厅、走廊、办公室可拍",
                    "compliance_risks": [],
                    "traffic_hooks": ["大屏公开", "手机录音"],
                },
            },
            "validation_errors": [],
            "repair_attempts": [],
            "first_attempt": {
                "provider_used": "mock-provider",
                "model_used": "mock-model",
                "usage": {},
            },
        }

    monkeypatch.setattr(
        story_outline_module, "generate_with_repair", _fake_generate_with_repair
    )

    class _Svc(StoryOutlineMixin):
        def __init__(self) -> None:
            self.story_agent = None
            self.ai_manager = object()
            self.logger = logging.getLogger(__name__)

    service = _Svc()
    result = await service.generate_story_outline(
        title="T",
        genre="drama",
        characters=[{"name": "Hero", "description": "lead"}],
        story_format="short_drama",
        generation_mode="production",
    )

    assert result is not None
    assert result["generation_mode"] == "production"
    assert result["production_mode"] is True
    prompt = captured["base_prompt"]
    assert "structured_story_contract" in prompt
    assert "大期待" in prompt
    assert "小期待阶梯" in prompt
    assert "信息差设计" in prompt
    assert "前三集立主线" in prompt
