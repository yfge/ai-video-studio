"""
重试准备节点单元测试

测试 Duration Orchestrator 的重试准备逻辑。
"""

import pytest

from app.services.duration_orchestrator.constants import MAX_RETRY_ATTEMPTS
from app.services.duration_orchestrator.nodes.prepare_retry import (
    prepare_retry_node,
    should_retry_or_fail,
)
from app.services.duration_orchestrator.state import SceneBudget, SceneStatus


class TestPrepareRetryNode:
    """测试重试准备节点"""

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
                    actual_duration_seconds=30,  # 太短
                    actual_word_count=68,
                    attempt_count=1,
                ),
            ],
            "current_scene_index": 0,
            "generated_dialogues": {
                1: [{"scene_number": 1, "content": "测试对白"}],
            },
            "reasoning": [],
        }

    def test_generates_adjustment_hint(self, base_state):
        """生成调整建议"""
        result = prepare_retry_node(base_state)

        budget = result["scene_budgets"][0]
        assert budget.adjustment_hint is not None
        assert budget.last_rejection_reason == "duration_too_short"

    def test_clears_generated_dialogues(self, base_state):
        """清空已生成的对白"""
        result = prepare_retry_node(base_state)

        assert 1 not in result["generated_dialogues"]

    def test_status_remains_pending(self, base_state):
        """状态保持为待处理"""
        result = prepare_retry_node(base_state)

        budget = result["scene_budgets"][0]
        assert budget.status == SceneStatus.PENDING

    def test_updates_reasoning(self, base_state):
        """更新推理日志"""
        result = prepare_retry_node(base_state)

        assert len(result["reasoning"]) > 0
        assert "重试" in result["reasoning"][0]

    def test_force_commit_at_max_retries(self, base_state):
        """达到最大重试次数时强制提交"""
        base_state["scene_budgets"][0].attempt_count = MAX_RETRY_ATTEMPTS

        result = prepare_retry_node(base_state)

        budget = result["scene_budgets"][0]
        assert budget.status == SceneStatus.COMMITTED
        assert budget.last_rejection_reason == "max_retries_exceeded"

    def test_index_out_of_bounds(self, base_state):
        """索引越界时返回空"""
        base_state["current_scene_index"] = 99

        result = prepare_retry_node(base_state)

        assert result == {}

    def test_duration_too_long_hint(self, base_state):
        """时长过长的调整建议"""
        base_state["scene_budgets"][0].actual_duration_seconds = 90  # 太长
        base_state["scene_budgets"][0].actual_word_count = 200

        result = prepare_retry_node(base_state)

        budget = result["scene_budgets"][0]
        assert budget.last_rejection_reason == "duration_too_long"
        assert "删减" in budget.adjustment_hint


class TestShouldRetryOrFail:
    """测试路由函数"""

    def test_retry_when_pending(self):
        """待处理时重试"""
        state = {
            "scene_budgets": [
                SceneBudget(
                    scene_number=1,
                    scene_index=0,
                    target_duration_seconds=60,
                    target_word_count=135,
                    min_duration_seconds=51,
                    max_duration_seconds=69,
                    status=SceneStatus.PENDING,
                    attempt_count=1,
                ),
            ],
            "current_scene_index": 0,
        }

        result = should_retry_or_fail(state)

        assert result == "retry"

    def test_commit_when_committed(self):
        """已提交时返回 commit"""
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
            ],
            "current_scene_index": 0,
        }

        result = should_retry_or_fail(state)

        assert result == "commit"

    def test_commit_at_max_retries(self):
        """达到最大重试次数时返回 commit"""
        state = {
            "scene_budgets": [
                SceneBudget(
                    scene_number=1,
                    scene_index=0,
                    target_duration_seconds=60,
                    target_word_count=135,
                    min_duration_seconds=51,
                    max_duration_seconds=69,
                    status=SceneStatus.PENDING,
                    attempt_count=MAX_RETRY_ATTEMPTS,
                ),
            ],
            "current_scene_index": 0,
        }

        result = should_retry_or_fail(state)

        assert result == "commit"

    def test_commit_when_index_exceeds(self):
        """索引超出时返回 commit"""
        state = {
            "scene_budgets": [],
            "current_scene_index": 0,
        }

        result = should_retry_or_fail(state)

        assert result == "commit"
