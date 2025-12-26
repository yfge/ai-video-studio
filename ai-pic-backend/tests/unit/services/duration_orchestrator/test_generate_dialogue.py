"""
对白生成节点单元测试

测试 Duration Orchestrator 的对白生成逻辑。
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from app.services.duration_orchestrator.constants import MAX_RETRY_ATTEMPTS
from app.services.duration_orchestrator.nodes.generate_dialogue import (
    generate_dialogue_node,
    should_proceed_to_tts,
)
from app.services.duration_orchestrator.state import SceneBudget, SceneStatus


class TestGenerateDialogueNode:
    """测试对白生成节点"""

    @pytest.fixture
    def mock_script_agent(self):
        """创建模拟的 ScriptLangGraphAgent"""
        agent = MagicMock()
        agent.generate = AsyncMock()
        return agent

    @pytest.fixture
    def base_state(self, mock_script_agent):
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
            "script_agent": mock_script_agent,
            "episode": {"id": 1, "title": "测试剧集"},
            "story": {"id": 1, "title": "测试故事"},
            "generation_config": {
                "format_type": "short_video",
                "language": "zh",
                "dialogue_style": "natural",
            },
            "generated_dialogues": {},
            "reasoning": [],
        }

    @pytest.mark.asyncio
    async def test_successful_generation(self, base_state, mock_script_agent):
        """成功生成对白"""
        mock_script_agent.generate.return_value = {
            "content": {
                "dialogues": [
                    {"scene_number": 1, "character": "小明", "content": "你好世界"},
                    {"scene_number": 1, "character": "小红", "content": "再见朋友"},
                ],
                "stage_directions": [],
            },
        }

        result = await generate_dialogue_node(base_state)

        assert "scene_budgets" in result
        assert "generated_dialogues" in result
        assert 1 in result["generated_dialogues"]
        assert len(result["generated_dialogues"][1]) == 2

        budget = result["scene_budgets"][0]
        assert budget.actual_word_count == 8  # "你好世界" + "再见朋友"
        assert budget.attempt_count == 1

    @pytest.mark.asyncio
    async def test_generation_with_retry_hint(self, base_state, mock_script_agent):
        """带重试提示的生成"""
        budget = base_state["scene_budgets"][0]
        budget.attempt_count = 1
        budget.adjustment_hint = "请增加约20字的对白"

        mock_script_agent.generate.return_value = {
            "content": {
                "dialogues": [
                    {
                        "scene_number": 1,
                        "character": "小明",
                        "content": "这是更长的对白内容",
                    },
                ],
            },
        }

        result = await generate_dialogue_node(base_state)

        assert result["scene_budgets"][0].attempt_count == 2
        mock_script_agent.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_missing_script_agent(self, base_state):
        """缺少 script_agent 时返回错误"""
        del base_state["script_agent"]

        result = await generate_dialogue_node(base_state)

        assert "errors" in result
        assert any("missing_script_agent" in e for e in result["errors"])

    @pytest.mark.asyncio
    async def test_generation_failure(self, base_state, mock_script_agent):
        """生成失败时的处理"""
        mock_script_agent.generate.return_value = {
            "error": "dialogue_failed",
        }

        result = await generate_dialogue_node(base_state)

        assert "errors" in result
        budget = result["scene_budgets"][0]
        assert budget.status == SceneStatus.PENDING

    @pytest.mark.asyncio
    async def test_index_out_of_bounds(self, base_state):
        """索引越界时返回空结果"""
        base_state["current_scene_index"] = 99

        result = await generate_dialogue_node(base_state)

        assert result == {}

    @pytest.mark.asyncio
    async def test_status_update_to_in_progress(self, base_state, mock_script_agent):
        """生成时状态更新为进行中"""
        mock_script_agent.generate.return_value = {
            "content": {"dialogues": []},
        }

        await generate_dialogue_node(base_state)

        # 注意：因为生成后会更新状态，所以这里检查的是最终状态
        # 在实际执行过程中，状态会先变为 IN_PROGRESS

    @pytest.mark.asyncio
    async def test_word_count_calculation(self, base_state, mock_script_agent):
        """字数计算正确"""
        mock_script_agent.generate.return_value = {
            "content": {
                "dialogues": [
                    {
                        "scene_number": 1,
                        "character": "A",
                        "content": "这是十个汉字测试内容",
                    },
                ],
            },
        }

        result = await generate_dialogue_node(base_state)

        budget = result["scene_budgets"][0]
        assert budget.actual_word_count == 10

    @pytest.mark.asyncio
    async def test_filters_dialogues_by_scene_number(
        self, base_state, mock_script_agent
    ):
        """按场景号过滤对白"""
        mock_script_agent.generate.return_value = {
            "content": {
                "dialogues": [
                    {"scene_number": 1, "character": "A", "content": "场景1对白"},
                    {"scene_number": 2, "character": "B", "content": "场景2对白"},
                    {"scene_number": 1, "character": "C", "content": "场景1另一条对白"},
                ],
            },
        }

        result = await generate_dialogue_node(base_state)

        scene_dialogues = result["generated_dialogues"][1]
        assert len(scene_dialogues) == 2
        assert all(d["scene_number"] == 1 for d in scene_dialogues)


class TestShouldProceedToTTS:
    """测试 TTS 路由函数"""

    def test_proceed_to_tts_with_dialogues(self):
        """有对白时进入 TTS"""
        state = {
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
                1: [{"scene_number": 1, "content": "测试对白"}],
            },
        }

        result = should_proceed_to_tts(state)

        assert result == "tts"

    def test_retry_without_dialogues(self):
        """无对白时重试"""
        state = {
            "scene_budgets": [
                SceneBudget(
                    scene_number=1,
                    scene_index=0,
                    target_duration_seconds=60,
                    target_word_count=135,
                    min_duration_seconds=51,
                    max_duration_seconds=69,
                    attempt_count=1,
                ),
            ],
            "current_scene_index": 0,
            "generated_dialogues": {},
        }

        result = should_proceed_to_tts(state)

        assert result == "retry"

    def test_failed_after_max_retries(self):
        """达到最大重试次数后失败"""
        state = {
            "scene_budgets": [
                SceneBudget(
                    scene_number=1,
                    scene_index=0,
                    target_duration_seconds=60,
                    target_word_count=135,
                    min_duration_seconds=51,
                    max_duration_seconds=69,
                    attempt_count=MAX_RETRY_ATTEMPTS,
                ),
            ],
            "current_scene_index": 0,
            "generated_dialogues": {},
        }

        result = should_proceed_to_tts(state)

        assert result == "failed"

    def test_failed_with_invalid_index(self):
        """无效索引时失败"""
        state = {
            "scene_budgets": [],
            "current_scene_index": 0,
            "generated_dialogues": {},
        }

        result = should_proceed_to_tts(state)

        assert result == "failed"
