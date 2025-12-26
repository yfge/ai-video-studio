"""
final_validation 节点单元测试

测试最终时长验证功能。
"""

import pytest

from app.services.duration_orchestrator.constants import (
    DURATION_TOLERANCE_EPISODE_HIGH,
    DURATION_TOLERANCE_EPISODE_LOW,
)
from app.services.duration_orchestrator.nodes.final_validation import (
    TOLERANCE_PERCENT,
    final_validation_node,
    should_pass_or_fail,
)


class TestFinalValidationNode:
    """测试 final_validation_node"""

    @pytest.fixture
    def base_state(self):
        """基础状态"""
        return {
            "episode_id": 1,
            "total_duration_minutes": 3,  # 180秒
            "statistics": {
                "total_actual_duration_seconds": 180.0,
            },
            "reasoning": [],
            "errors": [],
        }

    def test_validation_passes_exact_match(self, base_state):
        """测试精确匹配时验证通过"""
        result = final_validation_node(base_state)

        assert result["final_validation_result"]["passed"] is True
        assert result["success"] is True
        assert result["final_validation_result"]["duration_ratio"] == 1.0
        assert result["final_validation_result"]["deviation_percent"] == 0.0

    def test_validation_passes_within_tolerance(self, base_state):
        """测试在容差范围内验证通过"""
        # 设置实际时长为目标的 95%（在 ±10% 容差内）
        base_state["statistics"]["total_actual_duration_seconds"] = 171.0  # 95%

        result = final_validation_node(base_state)

        assert result["final_validation_result"]["passed"] is True
        assert result["success"] is True

    def test_validation_fails_too_short(self, base_state):
        """测试时长过短时验证失败"""
        # 设置实际时长为目标的 85%（超出 ±10% 容差）
        base_state["statistics"]["total_actual_duration_seconds"] = 153.0  # 85%

        result = final_validation_node(base_state)

        assert result["final_validation_result"]["passed"] is False
        assert result["success"] is False
        assert len(result["errors"]) > 0
        assert "过短" in result["errors"][0]

    def test_validation_fails_too_long(self, base_state):
        """测试时长过长时验证失败"""
        # 设置实际时长为目标的 115%（超出 ±10% 容差）
        base_state["statistics"]["total_actual_duration_seconds"] = 207.0  # 115%

        result = final_validation_node(base_state)

        assert result["final_validation_result"]["passed"] is False
        assert result["success"] is False
        assert len(result["errors"]) > 0
        assert "过长" in result["errors"][0]

    def test_validation_boundary_lower(self, base_state):
        """测试下边界（刚好在容差内）"""
        # 90% = 162秒
        base_state["statistics"]["total_actual_duration_seconds"] = 162.0

        result = final_validation_node(base_state)

        assert result["final_validation_result"]["passed"] is True

    def test_validation_boundary_upper(self, base_state):
        """测试上边界（刚好在容差内）"""
        # 110% = 198秒
        base_state["statistics"]["total_actual_duration_seconds"] = 198.0

        result = final_validation_node(base_state)

        assert result["final_validation_result"]["passed"] is True

    def test_validation_result_structure(self, base_state):
        """测试验证结果结构"""
        result = final_validation_node(base_state)

        validation = result["final_validation_result"]
        assert "passed" in validation
        assert "total_actual_duration_seconds" in validation
        assert "total_target_duration_seconds" in validation
        assert "duration_ratio" in validation
        assert "deviation_seconds" in validation
        assert "deviation_percent" in validation
        assert "tolerance_percent" in validation
        assert "tolerance_range" in validation

    def test_validation_tolerance_range(self, base_state):
        """测试容差范围计算"""
        result = final_validation_node(base_state)

        tolerance_range = result["final_validation_result"]["tolerance_range"]
        target = 180  # 3分钟

        # 验证容差范围 (使用 pytest.approx 处理浮点精度)
        expected_min = target * DURATION_TOLERANCE_EPISODE_LOW
        expected_max = target * DURATION_TOLERANCE_EPISODE_HIGH

        assert tolerance_range["min_seconds"] == pytest.approx(expected_min)
        assert tolerance_range["max_seconds"] == pytest.approx(expected_max)

    def test_validation_updates_reasoning_pass(self, base_state):
        """测试通过时更新推理日志"""
        result = final_validation_node(base_state)

        assert len(result["reasoning"]) > 0
        assert "通过" in result["reasoning"][-1]

    def test_validation_updates_reasoning_fail(self, base_state):
        """测试失败时更新推理日志"""
        base_state["statistics"]["total_actual_duration_seconds"] = 150.0

        result = final_validation_node(base_state)

        assert len(result["reasoning"]) > 0
        assert "失败" in result["reasoning"][-1]

    def test_validation_sets_phase(self, base_state):
        """测试设置阶段状态"""
        result = final_validation_node(base_state)

        assert result["phase"] == "validated"

    def test_validation_zero_target(self):
        """测试零目标时长"""
        state = {
            "episode_id": 1,
            "total_duration_minutes": 0,
            "statistics": {"total_actual_duration_seconds": 0},
            "reasoning": [],
            "errors": [],
        }

        result = final_validation_node(state)

        # 应该处理零除错误
        assert "final_validation_result" in result
        assert result["final_validation_result"]["duration_ratio"] == 0


class TestShouldPassOrFail:
    """测试 should_pass_or_fail 路由函数"""

    def test_returns_pass_when_passed(self):
        """测试通过时返回 pass"""
        state = {"final_validation_result": {"passed": True}}
        assert should_pass_or_fail(state) == "pass"

    def test_returns_fail_when_failed(self):
        """测试失败时返回 fail"""
        state = {"final_validation_result": {"passed": False}}
        assert should_pass_or_fail(state) == "fail"

    def test_returns_fail_when_no_result(self):
        """测试无结果时返回 fail"""
        state = {}
        assert should_pass_or_fail(state) == "fail"

    def test_returns_fail_when_empty_result(self):
        """测试空结果时返回 fail"""
        state = {"final_validation_result": {}}
        assert should_pass_or_fail(state) == "fail"
