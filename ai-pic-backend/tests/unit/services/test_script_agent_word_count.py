"""
ScriptLangGraphAgent 字数约束单元测试

测试 ScriptLangGraphAgent 的字数约束集成。
"""

from unittest.mock import MagicMock

import pytest
from app.services.duration_orchestrator.state import SceneBudget
from app.services.script_agent import ScriptLangGraphAgent


class TestBuildWordCountConstraints:
    """测试字数约束构建"""

    @pytest.fixture
    def mock_service(self):
        """创建模拟的 AIService"""
        service = MagicMock()
        service.ai_manager = MagicMock()
        return service

    @pytest.fixture
    def agent(self, mock_service):
        """创建 ScriptLangGraphAgent 实例"""
        return ScriptLangGraphAgent(mock_service)

    def test_empty_budgets_returns_empty_string(self, agent):
        """空预算列表返回空字符串"""
        result = agent._build_word_count_constraints([], [])
        assert result == ""

    def test_single_budget_constraint(self, agent):
        """单场景预算约束"""
        budgets = [
            SceneBudget(
                scene_number=1,
                scene_index=0,
                target_duration_seconds=60,
                target_word_count=135,
                min_duration_seconds=51,
                max_duration_seconds=69,
            ),
        ]
        scenes = [{"scene_number": 1, "summary": "测试场景"}]

        result = agent._build_word_count_constraints(budgets, scenes)

        assert "60 秒" in result
        assert "135" in result
        assert "51" in result
        assert "69" in result

    def test_multiple_budget_constraints(self, agent):
        """多场景预算约束"""
        budgets = [
            SceneBudget(
                scene_number=1,
                scene_index=0,
                target_duration_seconds=30,
                target_word_count=68,
                min_duration_seconds=26,
                max_duration_seconds=35,
            ),
            SceneBudget(
                scene_number=2,
                scene_index=1,
                target_duration_seconds=60,
                target_word_count=135,
                min_duration_seconds=51,
                max_duration_seconds=69,
            ),
        ]
        scenes = [
            {"scene_number": 1, "summary": "场景1"},
            {"scene_number": 2, "summary": "场景2"},
        ]

        result = agent._build_word_count_constraints(budgets, scenes)

        assert "场景 1" in result
        assert "场景 2" in result
        assert "30 秒" in result
        assert "60 秒" in result

    def test_retry_hint_included(self, agent):
        """重试提示被包含"""
        budgets = [
            SceneBudget(
                scene_number=1,
                scene_index=0,
                target_duration_seconds=60,
                target_word_count=135,
                min_duration_seconds=51,
                max_duration_seconds=69,
                attempt_count=1,
                adjustment_hint="请增加约30字的对白",
            ),
        ]
        scenes = [{"scene_number": 1}]

        result = agent._build_word_count_constraints(budgets, scenes)

        assert "调整建议" in result
        assert "增加约30字" in result
        assert "第 2 次重试" in result

    def test_no_retry_hint_for_first_attempt(self, agent):
        """首次尝试不包含重试提示"""
        budgets = [
            SceneBudget(
                scene_number=1,
                scene_index=0,
                target_duration_seconds=60,
                target_word_count=135,
                min_duration_seconds=51,
                max_duration_seconds=69,
                attempt_count=0,  # 首次尝试
            ),
        ]
        scenes = [{"scene_number": 1}]

        result = agent._build_word_count_constraints(budgets, scenes)

        assert "调整建议" not in result


class TestGenerateMethodSignature:
    """测试 generate 方法签名"""

    @pytest.fixture
    def mock_service(self):
        """创建模拟的 AIService"""
        service = MagicMock()
        service.ai_manager = None  # 模拟无 AI manager
        return service

    @pytest.fixture
    def agent(self, mock_service):
        """创建 ScriptLangGraphAgent 实例"""
        return ScriptLangGraphAgent(mock_service)

    @pytest.mark.asyncio
    async def test_accepts_scene_budgets_parameter(self, agent):
        """接受 scene_budgets 参数"""
        budgets = [
            SceneBudget(
                scene_number=1,
                scene_index=0,
                target_duration_seconds=60,
                target_word_count=135,
                min_duration_seconds=51,
                max_duration_seconds=69,
            ),
        ]

        # 应该能正常调用，不会抛出参数错误
        # 因为没有 ai_manager，会返回 None
        result = await agent.generate(
            episode={"id": 1},
            story={"id": 1},
            format_type="short_video",
            language="zh",
            dialogue_style="natural",
            scene_detail_level="detailed",
            additional_requirements=None,
            style_preferences=None,
            model=None,
            prefer_provider=None,
            temperature=0.7,
            scene_budgets=budgets,
        )

        # 无 AI manager 时返回 None
        assert result is None

    @pytest.mark.asyncio
    async def test_scene_budgets_optional(self, agent):
        """scene_budgets 参数可选"""
        # 不传 scene_budgets 应该也能正常调用
        result = await agent.generate(
            episode={"id": 1},
            story={"id": 1},
            format_type="short_video",
            language="zh",
            dialogue_style="natural",
            scene_detail_level="detailed",
            additional_requirements=None,
            style_preferences=None,
            model=None,
            prefer_provider=None,
            temperature=0.7,
        )

        # 无 AI manager 时返回 None
        assert result is None
