"""
时长验证节点

验证场景的实际 TTS 时长是否在目标范围内。
"""

import logging
from typing import Any, Dict

from app.services.duration_orchestrator.constants import MAX_RETRY_ATTEMPTS
from app.services.duration_orchestrator.state import SceneBudget, SceneStatus
from app.services.duration_orchestrator.utils import compute_adjustment_hint

logger = logging.getLogger(__name__)


def validate_duration_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    时长验证节点。

    验证当前场景的实际 TTS 时长是否在目标范围内。

    输入状态:
        - scene_budgets: 场景预算列表
        - current_scene_index: 当前场景索引

    输出状态更新:
        - scene_budgets: 更新验证结果
        - reasoning: 添加验证日志
    """
    budgets = state.get("scene_budgets", [])
    current_index = state.get("current_scene_index", 0)

    if current_index >= len(budgets):
        logger.warning("validate_duration_node: 当前索引越界")
        return {}

    budget: SceneBudget = budgets[current_index]

    # 检查是否有实际时长数据
    if budget.actual_duration_seconds is None:
        logger.warning(
            f"validate_duration_node: 场景 {budget.scene_number} 无实际时长数据"
        )
        return {}

    # 验证时长
    is_valid = budget.is_within_tolerance()
    ratio = budget.duration_ratio()

    logger.info(
        f"validate_duration_node: 场景 {budget.scene_number} 验证结果",
        extra={
            "scene_number": budget.scene_number,
            "target_duration": budget.target_duration_seconds,
            "actual_duration": budget.actual_duration_seconds,
            "ratio": ratio,
            "is_valid": is_valid,
            "attempt_count": budget.attempt_count,
        },
    )

    reasoning = state.get("reasoning", [])

    if is_valid:
        # 验证通过
        budget.status = SceneStatus.COMMITTED
        budget.last_rejection_reason = None
        budget.adjustment_hint = None

        reasoning.append(
            f"场景 {budget.scene_number} 验证通过: "
            f"{budget.actual_duration_seconds:.1f}s / "
            f"{budget.target_duration_seconds}s ({ratio:.0%})"
        )
    else:
        # 验证失败
        if budget.attempt_count >= MAX_RETRY_ATTEMPTS:
            # 达到最大重试次数，强制接受
            budget.status = SceneStatus.COMMITTED
            reasoning.append(
                f"场景 {budget.scene_number} 达到最大重试次数 ({MAX_RETRY_ATTEMPTS})，"
                f"强制接受: {budget.actual_duration_seconds:.1f}s / "
                f"{budget.target_duration_seconds}s ({ratio:.0%})"
            )
            logger.warning(f"场景 {budget.scene_number} 达到最大重试次数，强制接受")
        else:
            # 生成调整建议
            actual_ms = int(budget.actual_duration_seconds * 1000)
            actual_words = budget.actual_word_count or 0

            reason, hint = compute_adjustment_hint(
                actual_word_count=actual_words,
                actual_duration_ms=actual_ms,
                target_duration_seconds=budget.target_duration_seconds,
            )

            budget.status = SceneStatus.PENDING
            budget.last_rejection_reason = reason
            budget.adjustment_hint = hint

            reasoning.append(
                f"场景 {budget.scene_number} 验证失败 ({reason}): "
                f"{budget.actual_duration_seconds:.1f}s / "
                f"{budget.target_duration_seconds}s ({ratio:.0%})，"
                f"将进行第 {budget.attempt_count + 1} 次重试"
            )

    return {
        "scene_budgets": budgets,
        "reasoning": reasoning,
    }


def should_commit_or_retry(state: Dict[str, Any]) -> str:
    """
    路由函数：判断是否应该提交或重试当前场景。

    Returns:
        "commit" - 验证通过，提交场景
        "retry" - 验证失败，需要重试
        "next" - 进入下一个场景
    """
    budgets = state.get("scene_budgets", [])
    current_index = state.get("current_scene_index", 0)

    if current_index >= len(budgets):
        return "next"

    budget: SceneBudget = budgets[current_index]

    if budget.status == SceneStatus.COMMITTED:
        return "commit"
    elif budget.status == SceneStatus.PENDING and budget.last_rejection_reason:
        return "retry"
    else:
        return "next"


def check_all_scenes_done(state: Dict[str, Any]) -> str:
    """
    路由函数：检查是否所有场景都已处理完成。

    Returns:
        "done" - 所有场景已处理，进入组装阶段
        "continue" - 还有待处理的场景
    """
    budgets = state.get("scene_budgets", [])

    if not budgets:
        return "done"

    all_done = all(
        b.status in (SceneStatus.COMMITTED, SceneStatus.FAILED) for b in budgets
    )

    return "done" if all_done else "continue"
