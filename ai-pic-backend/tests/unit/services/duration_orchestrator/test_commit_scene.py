"""
场景提交节点单元测试

测试 Duration Orchestrator 的场景提交和预算再平衡逻辑。
"""

import pytest

from app.services.duration_orchestrator.nodes.commit_scene import (
    commit_scene_node,
    should_continue_or_assemble,
)
from app.services.duration_orchestrator.state import SceneBudget, SceneStatus


class TestCommitSceneNode:
    """测试场景提交节点"""

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
                    actual_duration_seconds=55,
                    attempt_count=1,
                ),
                SceneBudget(
                    scene_number=2,
                    scene_index=1,
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
            "committed_scenes": {},
            "reasoning": [],
        }

    def test_commit_scene_status(self, base_state):
        """提交后状态变为 COMMITTED"""
        result = commit_scene_node(base_state)

        budget = result["scene_budgets"][0]
        assert budget.status == SceneStatus.COMMITTED

    def test_commit_saves_scene_data(self, base_state):
        """提交后保存场景数据"""
        result = commit_scene_node(base_state)

        assert 1 in result["committed_scenes"]
        committed = result["committed_scenes"][1]
        assert committed["scene_number"] == 1
        assert committed["target_duration_seconds"] == 60
        assert committed["actual_duration_seconds"] == 55
        assert committed["deviation_seconds"] == -5
        assert committed["attempt_count"] == 1

    def test_commit_moves_to_next_scene(self, base_state):
        """提交后移动到下一个场景"""
        result = commit_scene_node(base_state)

        assert result["current_scene_index"] == 1

    def test_commit_triggers_rebalance_when_over(self, base_state):
        """超时时触发再平衡"""
        # 场景1实际70秒，目标60秒，超时10秒
        base_state["scene_budgets"][0].actual_duration_seconds = 70

        result = commit_scene_node(base_state)

        # 场景2的目标应该被调整（减少5秒，因为有1个后续场景）
        budget2 = result["scene_budgets"][1]
        assert budget2.target_duration_seconds == 50  # 60 - 10

    def test_commit_triggers_rebalance_when_under(self, base_state):
        """欠时时触发再平衡"""
        # 场景1实际40秒，目标60秒，欠时20秒
        base_state["scene_budgets"][0].actual_duration_seconds = 40

        result = commit_scene_node(base_state)

        # 场景2的目标应该被调整（增加20秒）
        budget2 = result["scene_budgets"][1]
        assert budget2.target_duration_seconds == 80  # 60 + 20

    def test_commit_no_rebalance_for_last_scene(self, base_state):
        """最后一个场景不触发再平衡"""
        base_state["current_scene_index"] = 1
        base_state["scene_budgets"][1].actual_duration_seconds = 70

        result = commit_scene_node(base_state)

        # 没有后续场景，不需要再平衡
        assert result["current_scene_index"] == 2

    def test_commit_updates_reasoning(self, base_state):
        """提交后更新推理日志"""
        result = commit_scene_node(base_state)

        assert len(result["reasoning"]) > 0
        assert "已提交" in result["reasoning"][0]

    def test_commit_index_out_of_bounds(self, base_state):
        """索引越界时返回空"""
        base_state["current_scene_index"] = 99

        result = commit_scene_node(base_state)

        assert result == {}


class TestShouldContinueOrAssemble:
    """测试路由函数"""

    def test_continue_when_pending_scenes(self):
        """还有待处理场景时继续"""
        state = {
            "scene_budgets": [
                SceneBudget(
                    scene_number=1,
                    scene_index=0,
                    target_duration_seconds=60,
                    target_word_count=135,
                    min_duration_seconds=51,
                    max_duration_seconds=69,
                    status=SceneStatus.COMMITTED,
                ),
                SceneBudget(
                    scene_number=2,
                    scene_index=1,
                    target_duration_seconds=60,
                    target_word_count=135,
                    min_duration_seconds=51,
                    max_duration_seconds=69,
                    status=SceneStatus.PENDING,
                ),
            ],
            "current_scene_index": 1,
        }

        result = should_continue_or_assemble(state)

        assert result == "continue"

    def test_assemble_when_all_committed(self):
        """所有场景已提交时进入组装"""
        state = {
            "scene_budgets": [
                SceneBudget(
                    scene_number=1,
                    scene_index=0,
                    target_duration_seconds=60,
                    target_word_count=135,
                    min_duration_seconds=51,
                    max_duration_seconds=69,
                    status=SceneStatus.COMMITTED,
                ),
                SceneBudget(
                    scene_number=2,
                    scene_index=1,
                    target_duration_seconds=60,
                    target_word_count=135,
                    min_duration_seconds=51,
                    max_duration_seconds=69,
                    status=SceneStatus.COMMITTED,
                ),
            ],
            "current_scene_index": 2,
        }

        result = should_continue_or_assemble(state)

        assert result == "assemble"

    def test_assemble_when_index_exceeds(self):
        """索引超出时进入组装"""
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
            "current_scene_index": 5,
        }

        result = should_continue_or_assemble(state)

        assert result == "assemble"
