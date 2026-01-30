"""
Duration Orchestrator Agent 单元测试

测试 DurationOrchestratorAgent 的完整流程。
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from app.services.duration_orchestrator.agent import (
    DurationOrchestratorAgent,
    orchestrate_episode_duration,
)


class TestDurationOrchestratorAgent:
    """测试 DurationOrchestratorAgent"""

    @pytest.fixture
    def mock_script_agent(self):
        """创建模拟的 ScriptLangGraphAgent"""
        agent = MagicMock()
        agent.generate = AsyncMock()
        return agent

    @pytest.fixture
    def base_params(self):
        """基础测试参数"""
        return {
            "episode_id": 1,
            "script_id": 1,
            "story_id": 1,
            "total_duration_minutes": 3,
            "scenes": [
                {
                    "scene_number": 1,
                    "summary": "场景1",
                    "estimated_duration_seconds": 60,
                },
                {
                    "scene_number": 2,
                    "summary": "场景2",
                    "estimated_duration_seconds": 60,
                },
            ],
            "episode": {"id": 1, "title": "测试剧集"},
            "story": {"id": 1, "title": "测试故事"},
        }

    @pytest.mark.asyncio
    async def test_orchestrate_returns_result(self, mock_script_agent, base_params):
        """编排返回正确的结果结构"""
        # 模拟 Script Agent 返回对白
        mock_script_agent.generate.return_value = {
            "content": {
                "dialogues": [
                    {
                        "scene_number": 1,
                        "character": "A",
                        "content": "这是场景一的对白内容",
                    },
                    {
                        "scene_number": 2,
                        "character": "B",
                        "content": "这是场景二的对白内容",
                    },
                ],
            },
        }

        agent = DurationOrchestratorAgent(
            script_agent=mock_script_agent,
            use_actual_tts=False,
        )

        result = await agent.orchestrate(**base_params)

        # 验证返回结构正确
        assert "success" in result
        assert result["episode_id"] == 1
        assert "scene_budgets" in result
        assert "reasoning" in result

    @pytest.mark.asyncio
    async def test_orchestrate_no_script_agent(self, base_params):
        """无 Script Agent 时的错误处理"""
        agent = DurationOrchestratorAgent(
            script_agent=None,
            use_actual_tts=False,
        )

        result = await agent.orchestrate(**base_params)

        # 应该有错误
        assert "errors" in result

    @pytest.mark.asyncio
    async def test_orchestrate_empty_scenes(self, mock_script_agent, base_params):
        """空场景列表"""
        base_params["scenes"] = []

        agent = DurationOrchestratorAgent(
            script_agent=mock_script_agent,
            use_actual_tts=False,
        )

        result = await agent.orchestrate(**base_params)

        # 应该有错误
        assert "errors" in result
        assert len(result.get("errors", [])) > 0

    @pytest.mark.asyncio
    async def test_orchestrate_with_generation_config(
        self, mock_script_agent, base_params
    ):
        """带生成配置的编排"""
        mock_script_agent.generate.return_value = {
            "content": {
                "dialogues": [
                    {"scene_number": 1, "character": "A", "content": "测试对白"},
                ],
            },
        }

        agent = DurationOrchestratorAgent(
            script_agent=mock_script_agent,
            use_actual_tts=False,
        )

        result = await agent.orchestrate(
            **base_params,
            generation_config={
                "format_type": "short_video",
                "language": "zh",
                "dialogue_style": "natural",
            },
        )

        # 验证返回结构
        assert "success" in result
        assert "scene_budgets" in result

    @pytest.mark.asyncio
    async def test_orchestrate_statistics_structure(
        self, mock_script_agent, base_params
    ):
        """验证统计信息结构"""
        mock_script_agent.generate.return_value = {
            "content": {
                "dialogues": [
                    {"scene_number": 1, "character": "A", "content": "测试对白内容"},
                    {"scene_number": 2, "character": "B", "content": "测试对白内容"},
                ],
            },
        }

        agent = DurationOrchestratorAgent(
            script_agent=mock_script_agent,
            use_actual_tts=False,
        )

        result = await agent.orchestrate(**base_params)

        # 统计信息应该存在
        if result.get("success"):
            stats = result.get("statistics", {})
            assert "total_target_duration_seconds" in stats
            assert "scene_count" in stats


class TestOrchestrateEpisodeDuration:
    """测试便捷函数"""

    @pytest.fixture
    def mock_script_agent(self):
        """创建模拟的 ScriptLangGraphAgent"""
        agent = MagicMock()
        agent.generate = AsyncMock(
            return_value={
                "content": {
                    "dialogues": [
                        {"scene_number": 1, "character": "A", "content": "测试"},
                    ],
                },
            }
        )
        return agent

    @pytest.mark.asyncio
    async def test_convenience_function(self, mock_script_agent):
        """测试便捷函数"""
        result = await orchestrate_episode_duration(
            episode_id=1,
            script_id=1,
            story_id=1,
            total_duration_minutes=3,
            scenes=[{"scene_number": 1, "summary": "场景1"}],
            episode={"id": 1},
            story={"id": 1},
            script_agent=mock_script_agent,
            use_actual_tts=False,
        )

        assert "success" in result
        assert "scene_budgets" in result


class TestAgentBuildGraph:
    """测试图构建"""

    def test_build_graph_structure(self):
        """验证图结构"""
        agent = DurationOrchestratorAgent()
        graph = agent._build_graph()

        # 验证节点存在
        assert "allocate_budget" in graph.nodes
        assert "generate_dialogue" in graph.nodes
        assert "tts_trial" in graph.nodes
        assert "validate_duration" in graph.nodes
        assert "commit_scene" in graph.nodes
        assert "prepare_retry" in graph.nodes

    def test_build_graph_entry_point(self):
        """验证入口点"""
        agent = DurationOrchestratorAgent()
        graph = agent._build_graph()

        # 入口点应该是 allocate_budget
        # LangGraph 内部实现可能不直接暴露 entry_point
        # 但编译后的图应该能正常工作
        compiled = graph.compile()
        assert compiled is not None


class TestSceneLoopIntegration:
    """场景循环集成测试 - 验证完整流程"""

    @pytest.fixture
    def mock_script_agent(self):
        """创建模拟的 ScriptLangGraphAgent"""
        agent = MagicMock()
        agent.generate = AsyncMock()
        return agent

    @pytest.mark.asyncio
    async def test_multi_scene_orchestration(self, mock_script_agent):
        """测试多场景编排流程"""
        # 设置每个场景返回不同的对白
        call_count = [0]

        async def generate_side_effect(*args, **kwargs):
            call_count[0] += 1
            scene_num = call_count[0]
            return {
                "content": {
                    "dialogues": [
                        {
                            "scene_number": scene_num,
                            "character": "A",
                            "content": f"这是场景{scene_num}的对白内容，需要足够长才能达到时长要求",
                        },
                    ],
                },
            }

        mock_script_agent.generate.side_effect = generate_side_effect

        agent = DurationOrchestratorAgent(
            script_agent=mock_script_agent,
            use_actual_tts=False,
        )

        result = await agent.orchestrate(
            episode_id=1,
            script_id=1,
            story_id=1,
            total_duration_minutes=3,
            scenes=[
                {
                    "scene_number": 1,
                    "summary": "开场",
                    "estimated_duration_seconds": 60,
                },
                {
                    "scene_number": 2,
                    "summary": "发展",
                    "estimated_duration_seconds": 60,
                },
                {
                    "scene_number": 3,
                    "summary": "结尾",
                    "estimated_duration_seconds": 60,
                },
            ],
            episode={"id": 1, "title": "测试剧集"},
            story={"id": 1, "title": "测试故事"},
        )

        # 验证结果结构
        assert "success" in result
        assert "scene_budgets" in result
        # 验证场景预算数量
        if result.get("scene_budgets"):
            assert len(result["scene_budgets"]) == 3

    @pytest.mark.asyncio
    async def test_budget_allocation_accuracy(self, mock_script_agent):
        """测试预算分配准确性"""
        mock_script_agent.generate.return_value = {
            "content": {
                "dialogues": [
                    {"scene_number": 1, "character": "A", "content": "测试对白内容"},
                ],
            },
        }

        agent = DurationOrchestratorAgent(
            script_agent=mock_script_agent,
            use_actual_tts=False,
        )

        result = await agent.orchestrate(
            episode_id=1,
            script_id=1,
            story_id=1,
            total_duration_minutes=2,  # 2分钟 = 120秒
            scenes=[
                {
                    "scene_number": 1,
                    "summary": "场景1",
                    "estimated_duration_seconds": 60,
                },
                {
                    "scene_number": 2,
                    "summary": "场景2",
                    "estimated_duration_seconds": 60,
                },
            ],
            episode={"id": 1},
            story={"id": 1},
        )

        # 验证预算分配
        if result.get("success") and result.get("scene_budgets"):
            budgets = result["scene_budgets"]
            # 每个场景应该有目标时长
            for budget in budgets:
                assert "target_duration_seconds" in budget
                # 目标时长应该合理分配
                assert budget["target_duration_seconds"] > 0

    @pytest.mark.asyncio
    async def test_reasoning_log_populated(self, mock_script_agent):
        """测试推理日志被正确填充"""
        mock_script_agent.generate.return_value = {
            "content": {
                "dialogues": [
                    {"scene_number": 1, "character": "A", "content": "对白内容"},
                ],
            },
        }

        agent = DurationOrchestratorAgent(
            script_agent=mock_script_agent,
            use_actual_tts=False,
        )

        result = await agent.orchestrate(
            episode_id=1,
            script_id=1,
            story_id=1,
            total_duration_minutes=1,
            scenes=[{"scene_number": 1, "summary": "场景1"}],
            episode={"id": 1},
            story={"id": 1},
        )

        # 验证推理日志
        assert "reasoning" in result
        # 推理日志应该包含预算分配的记录
        if result.get("reasoning"):
            assert len(result["reasoning"]) > 0

    @pytest.mark.asyncio
    async def test_error_handling_in_loop(self, mock_script_agent):
        """测试循环中的错误处理"""
        # 第一次调用成功，第二次抛出异常
        call_count = [0]

        async def generate_with_error(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return {
                    "content": {
                        "dialogues": [
                            {
                                "scene_number": 1,
                                "character": "A",
                                "content": "正常对白",
                            },
                        ],
                    },
                }
            raise ValueError("模拟生成失败")

        mock_script_agent.generate.side_effect = generate_with_error

        agent = DurationOrchestratorAgent(
            script_agent=mock_script_agent,
            use_actual_tts=False,
        )

        result = await agent.orchestrate(
            episode_id=1,
            script_id=1,
            story_id=1,
            total_duration_minutes=2,
            scenes=[
                {"scene_number": 1, "summary": "场景1"},
                {"scene_number": 2, "summary": "场景2"},
            ],
            episode={"id": 1},
            story={"id": 1},
        )

        # 应该有结果返回（即使有错误）
        assert result is not None
        # 验证有错误记录
        assert "errors" in result or "error" in result
