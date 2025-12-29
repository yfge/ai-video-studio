"""
预算分配单元测试

测试 Duration Orchestrator 的预算分配逻辑。
"""

import pytest

from app.services.duration_orchestrator.constants import (
    BUFFER_RATIO,
    DEFAULT_SCENE_DURATION_SECONDS,
    DIALOGUE_DENSITY_FACTOR,
    DURATION_TOLERANCE_SCENE_HIGH,
    DURATION_TOLERANCE_SCENE_LOW,
    MAX_SCENE_DURATION_SECONDS,
    MIN_SCENE_DURATION_SECONDS,
    WORDS_PER_SECOND,
)
from app.services.duration_orchestrator.state import SceneBudget, SceneStatus
from app.services.duration_orchestrator.utils import (
    allocate_scene_budgets,
    calculate_target_word_count,
    compute_adjustment_hint,
    count_dialogue_words,
    estimate_duration_from_words,
    rebalance_remaining_budgets,
)


class TestCalculateTargetWordCount:
    """测试字数计算

    新公式考虑对白密度因子 (DIALOGUE_DENSITY_FACTOR = 0.90):
    目标字数 = 时长(秒) * 对白密度 * 语速
    """

    def test_normal_duration(self):
        """正常时长的字数计算"""
        word_count = calculate_target_word_count(60)
        # 60秒 * 对白密度 * 语速
        expected = int(60 * DIALOGUE_DENSITY_FACTOR * WORDS_PER_SECOND)
        assert word_count == expected

    def test_short_duration(self):
        """短时长的字数计算"""
        word_count = calculate_target_word_count(10)
        # 10秒 * 对白密度 * 语速
        expected = int(10 * DIALOGUE_DENSITY_FACTOR * WORDS_PER_SECOND)
        assert word_count == expected

    def test_long_duration(self):
        """长时长的字数计算"""
        word_count = calculate_target_word_count(180)
        # 180秒 * 对白密度 * 语速
        expected = int(180 * DIALOGUE_DENSITY_FACTOR * WORDS_PER_SECOND)
        assert word_count == expected


class TestAllocateSceneBudgets:
    """测试预算分配"""

    def test_empty_scenes(self):
        """空场景列表"""
        budgets, buffer = allocate_scene_budgets(
            total_duration_minutes=3,
            scenes=[],
        )
        assert budgets == []
        assert buffer == 0

    def test_single_scene_no_estimate(self):
        """单场景无估算时长"""
        scenes = [{"scene_number": 1, "summary": "场景1"}]
        budgets, buffer = allocate_scene_budgets(
            total_duration_minutes=3,  # 180秒
            scenes=scenes,
        )

        assert len(budgets) == 1
        assert buffer == int(180 * BUFFER_RATIO)  # 9秒

        # 可分配时间 = 180 - 9 = 171秒
        budget = budgets[0]
        assert budget.scene_number == 1
        assert budget.target_duration_seconds <= 171
        assert budget.target_duration_seconds >= MIN_SCENE_DURATION_SECONDS

    def test_multiple_scenes_with_estimates(self):
        """多场景有估算时长，按比例分配"""
        scenes = [
            {"scene_number": 1, "estimated_duration_seconds": 30},
            {"scene_number": 2, "estimated_duration_seconds": 60},
            {"scene_number": 3, "estimated_duration_seconds": 30},
        ]
        budgets, buffer = allocate_scene_budgets(
            total_duration_minutes=3,  # 180秒
            scenes=scenes,
        )

        assert len(budgets) == 3
        assert buffer == int(180 * BUFFER_RATIO)

        # 场景2应该分配最多时间（比例 60/120 = 0.5）
        assert budgets[1].target_duration_seconds > budgets[0].target_duration_seconds
        assert budgets[1].target_duration_seconds > budgets[2].target_duration_seconds

        # 场景1和场景3应该相等（都是30秒，比例相同）
        assert budgets[0].target_duration_seconds == budgets[2].target_duration_seconds

    def test_word_count_calculated(self):
        """字数目标正确计算 (考虑对白密度因子)"""
        scenes = [{"scene_number": 1, "estimated_duration_seconds": 60}]
        budgets, _ = allocate_scene_budgets(
            total_duration_minutes=2,
            scenes=scenes,
        )

        budget = budgets[0]
        # 新公式: 字数 = 时长 * 对白密度 * 语速
        expected_words = int(
            budget.target_duration_seconds * DIALOGUE_DENSITY_FACTOR * WORDS_PER_SECOND
        )
        assert budget.target_word_count == expected_words

    def test_tolerance_range_calculated(self):
        """容差范围正确计算"""
        scenes = [{"scene_number": 1, "estimated_duration_seconds": 60}]
        budgets, _ = allocate_scene_budgets(
            total_duration_minutes=2,
            scenes=scenes,
        )

        budget = budgets[0]
        expected_min = int(budget.target_duration_seconds * DURATION_TOLERANCE_SCENE_LOW)
        expected_max = int(budget.target_duration_seconds * DURATION_TOLERANCE_SCENE_HIGH)
        assert budget.min_duration_seconds == expected_min
        assert budget.max_duration_seconds == expected_max

    def test_scene_duration_limits(self):
        """场景时长不超过最大/最小限制"""
        # 极短总时长
        scenes = [{"scene_number": 1}]
        budgets, _ = allocate_scene_budgets(
            total_duration_minutes=0.1,  # 6秒
            scenes=scenes,
        )
        assert budgets[0].target_duration_seconds >= MIN_SCENE_DURATION_SECONDS

        # 极长总时长，单场景
        budgets2, _ = allocate_scene_budgets(
            total_duration_minutes=10,  # 600秒
            scenes=scenes,
        )
        assert budgets2[0].target_duration_seconds <= MAX_SCENE_DURATION_SECONDS


class TestComputeAdjustmentHint:
    """测试调整建议生成"""

    def test_duration_too_short(self):
        """时长不足的调整建议"""
        reason, hint = compute_adjustment_hint(
            actual_word_count=50,
            actual_duration_ms=20000,  # 20秒
            target_duration_seconds=45,  # 45秒
        )

        assert reason == "duration_too_short"
        assert "20.0 秒" in hint
        assert "45 秒" in hint
        assert "增加" in hint

    def test_duration_too_long(self):
        """时长过长的调整建议"""
        reason, hint = compute_adjustment_hint(
            actual_word_count=200,
            actual_duration_ms=80000,  # 80秒
            target_duration_seconds=45,  # 45秒
        )

        assert reason == "duration_too_long"
        assert "80.0 秒" in hint
        assert "45 秒" in hint
        assert "删减" in hint

    def test_suggestion_includes_word_count(self):
        """建议包含字数估算"""
        reason, hint = compute_adjustment_hint(
            actual_word_count=50,
            actual_duration_ms=20000,
            target_duration_seconds=45,
        )

        # 差距 25 秒，约 62 字
        assert "字" in hint


class TestSceneBudget:
    """测试 SceneBudget 数据类"""

    def test_is_within_tolerance_true(self):
        """时长在容差范围内"""
        budget = SceneBudget(
            scene_number=1,
            scene_index=0,
            target_duration_seconds=60,
            target_word_count=135,
            min_duration_seconds=51,  # 60 * 0.85
            max_duration_seconds=69,  # 60 * 1.15
            actual_duration_seconds=55,
        )
        assert budget.is_within_tolerance() is True

    def test_is_within_tolerance_false_too_short(self):
        """时长过短"""
        budget = SceneBudget(
            scene_number=1,
            scene_index=0,
            target_duration_seconds=60,
            target_word_count=135,
            min_duration_seconds=51,
            max_duration_seconds=69,
            actual_duration_seconds=40,
        )
        assert budget.is_within_tolerance() is False

    def test_is_within_tolerance_false_too_long(self):
        """时长过长"""
        budget = SceneBudget(
            scene_number=1,
            scene_index=0,
            target_duration_seconds=60,
            target_word_count=135,
            min_duration_seconds=51,
            max_duration_seconds=69,
            actual_duration_seconds=80,
        )
        assert budget.is_within_tolerance() is False

    def test_duration_ratio(self):
        """时长比例计算"""
        budget = SceneBudget(
            scene_number=1,
            scene_index=0,
            target_duration_seconds=60,
            target_word_count=135,
            min_duration_seconds=51,
            max_duration_seconds=69,
            actual_duration_seconds=45,
        )
        assert budget.duration_ratio() == 0.75

    def test_duration_diff_seconds(self):
        """时长差异计算"""
        budget = SceneBudget(
            scene_number=1,
            scene_index=0,
            target_duration_seconds=60,
            target_word_count=135,
            min_duration_seconds=51,
            max_duration_seconds=69,
            actual_duration_seconds=75,
        )
        assert budget.duration_diff_seconds() == 15  # 超时 15 秒

    def test_to_dict(self):
        """转换为字典"""
        budget = SceneBudget(
            scene_number=1,
            scene_index=0,
            target_duration_seconds=60,
            target_word_count=135,
            min_duration_seconds=51,
            max_duration_seconds=69,
        )
        d = budget.to_dict()
        assert d["scene_number"] == 1
        assert d["target_duration_seconds"] == 60
        assert d["status"] == "pending"


class TestRebalanceRemainingBudgets:
    """测试预算再平衡"""

    def test_rebalance_when_over_budget(self):
        """超时时从后续场景扣除"""
        budgets = [
            SceneBudget(
                scene_number=1,
                scene_index=0,
                target_duration_seconds=30,
                target_word_count=68,
                min_duration_seconds=26,
                max_duration_seconds=35,
                status=SceneStatus.COMMITTED,
                actual_duration_seconds=40,  # 超时 10 秒
            ),
            SceneBudget(
                scene_number=2,
                scene_index=1,
                target_duration_seconds=30,
                target_word_count=68,
                min_duration_seconds=26,
                max_duration_seconds=35,
            ),
            SceneBudget(
                scene_number=3,
                scene_index=2,
                target_duration_seconds=30,
                target_word_count=68,
                min_duration_seconds=26,
                max_duration_seconds=35,
            ),
        ]

        rebalance_remaining_budgets(budgets, 0, 40)

        # 后续两个场景应该各减少 5 秒
        assert budgets[1].target_duration_seconds == 25
        assert budgets[2].target_duration_seconds == 25

    def test_rebalance_when_under_budget(self):
        """欠时时给后续场景增加"""
        budgets = [
            SceneBudget(
                scene_number=1,
                scene_index=0,
                target_duration_seconds=30,
                target_word_count=68,
                min_duration_seconds=26,
                max_duration_seconds=35,
                status=SceneStatus.COMMITTED,
                actual_duration_seconds=20,  # 欠时 10 秒
            ),
            SceneBudget(
                scene_number=2,
                scene_index=1,
                target_duration_seconds=30,
                target_word_count=68,
                min_duration_seconds=26,
                max_duration_seconds=35,
            ),
        ]

        rebalance_remaining_budgets(budgets, 0, 20)

        # 后续场景应该增加 10 秒
        assert budgets[1].target_duration_seconds == 40

    def test_no_rebalance_for_last_scene(self):
        """最后一个场景不需要再平衡"""
        budgets = [
            SceneBudget(
                scene_number=1,
                scene_index=0,
                target_duration_seconds=30,
                target_word_count=68,
                min_duration_seconds=26,
                max_duration_seconds=35,
            ),
        ]

        original_target = budgets[0].target_duration_seconds
        rebalance_remaining_budgets(budgets, 0, 40)

        # 不应该有变化
        assert budgets[0].target_duration_seconds == original_target


class TestCountDialogueWords:
    """测试对白字数统计"""

    def test_count_words(self):
        """正常对白字数统计"""
        dialogues = [
            {"character": "小明", "content": "你好世界"},
            {"character": "小红", "content": "再见朋友"},
        ]
        assert count_dialogue_words(dialogues) == 8

    def test_empty_dialogues(self):
        """空对白列表"""
        assert count_dialogue_words([]) == 0

    def test_empty_content(self):
        """空内容"""
        dialogues = [
            {"character": "小明", "content": ""},
            {"character": "小红", "content": "你好"},
        ]
        assert count_dialogue_words(dialogues) == 2


class TestEstimateDurationFromWords:
    """测试根据字数估算时长"""

    def test_estimate_duration(self):
        """正常字数估算时长"""
        word_count = int(60 * WORDS_PER_SECOND)
        assert estimate_duration_from_words(word_count) == 60

    def test_estimate_zero_words(self):
        """零字数"""
        assert estimate_duration_from_words(0) == 0
