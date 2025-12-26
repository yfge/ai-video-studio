"""
TTS 试跑节点单元测试

测试 Duration Orchestrator 的 TTS 时长估算逻辑。
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.duration_orchestrator.nodes.tts_trial import (
    estimate_duration_from_dialogues,
    tts_trial_node,
)
from app.services.duration_orchestrator.state import SceneBudget


class TestEstimateDurationFromDialogues:
    """测试对白时长估算"""

    def test_estimate_normal_dialogues(self):
        """正常对白的时长估算"""
        dialogues = [
            {"character": "小明", "content": "你好世界"},  # 4 chars
            {"character": "小红", "content": "再见朋友"},  # 4 chars
        ]
        # 8 chars / 2.25 chars/s = 3.56s = 3556ms
        duration_ms = estimate_duration_from_dialogues(dialogues)
        assert 3500 <= duration_ms <= 3600

    def test_estimate_empty_dialogues(self):
        """空对白列表"""
        duration_ms = estimate_duration_from_dialogues([])
        assert duration_ms == 0

    def test_estimate_with_custom_rate(self):
        """自定义语速"""
        dialogues = [{"content": "测试内容测试内容"}]  # 8 chars
        # 8 chars / 4 chars/s = 2s = 2000ms
        duration_ms = estimate_duration_from_dialogues(dialogues, speaking_rate=4.0)
        assert duration_ms == 2000

    def test_estimate_long_dialogue(self):
        """长对白的时长估算"""
        # 135 chars should be ~60 seconds (135 / 2.25 = 60)
        long_text = "这是一段" * 33 + "话"  # 133 chars
        dialogues = [{"content": long_text}]
        duration_ms = estimate_duration_from_dialogues(dialogues)
        assert 58000 <= duration_ms <= 62000  # ~60 seconds


class TestTtsTrialNode:
    """测试 TTS 试跑节点"""

    @pytest.fixture
    def base_state(self):
        """基础测试状态"""
        return {
            "scene_budgets": [
                SceneBudget(
                    scene_number=1,
                    scene_index=0,
                    target_duration_seconds=60,
                    target_word_count=135,
                    min_duration_seconds=51,
                    max_duration_seconds=69,
                ),
            ],
            "current_scene_index": 0,
            "generated_dialogues": {
                1: [
                    {"scene_number": 1, "character": "小明", "content": "你好世界"},
                    {"scene_number": 1, "character": "小红", "content": "再见朋友"},
                ],
            },
            "reasoning": [],
            "use_actual_tts": False,
        }

    @pytest.mark.asyncio
    async def test_estimate_mode(self, base_state):
        """估算模式"""
        result = await tts_trial_node(base_state)

        assert "scene_budgets" in result
        budget = result["scene_budgets"][0]
        assert budget.actual_duration_seconds is not None
        assert budget.actual_duration_seconds > 0

    @pytest.mark.asyncio
    async def test_updates_reasoning(self, base_state):
        """更新推理日志"""
        result = await tts_trial_node(base_state)

        assert "reasoning" in result
        assert len(result["reasoning"]) > 0
        assert "字数估算" in result["reasoning"][0]

    @pytest.mark.asyncio
    async def test_no_dialogues(self, base_state):
        """无对白时返回空"""
        base_state["generated_dialogues"] = {}

        result = await tts_trial_node(base_state)

        assert result == {}

    @pytest.mark.asyncio
    async def test_index_out_of_bounds(self, base_state):
        """索引越界"""
        base_state["current_scene_index"] = 99

        result = await tts_trial_node(base_state)

        assert result == {}

    @pytest.mark.asyncio
    async def test_actual_tts_mode_fallback(self, base_state):
        """实际 TTS 模式降级为估算"""
        base_state["use_actual_tts"] = True
        # 没有 tts_service，应该降级为估算模式

        result = await tts_trial_node(base_state)

        assert "scene_budgets" in result
        budget = result["scene_budgets"][0]
        assert budget.actual_duration_seconds is not None

    @pytest.mark.asyncio
    async def test_actual_tts_mode_with_service(self, base_state):
        """实际 TTS 模式有服务"""
        mock_tts_service = MagicMock()
        mock_tts_service.generate_speech = AsyncMock(
            return_value={"duration": 2.5}  # 2.5 seconds
        )

        base_state["use_actual_tts"] = True
        base_state["tts_service"] = mock_tts_service
        base_state["voice_config"] = {"voice_type": "test"}

        result = await tts_trial_node(base_state)

        assert "scene_budgets" in result
        budget = result["scene_budgets"][0]
        assert budget.actual_duration_seconds is not None
        # TTS was called
        assert mock_tts_service.generate_speech.called

    @pytest.mark.asyncio
    async def test_calculates_deviation(self, base_state):
        """计算偏差"""
        result = await tts_trial_node(base_state)

        # 8 chars / 2.25 = 3.56s, target is 60s
        # deviation should be negative (too short)
        budget = result["scene_budgets"][0]
        assert budget.actual_duration_seconds < budget.target_duration_seconds
