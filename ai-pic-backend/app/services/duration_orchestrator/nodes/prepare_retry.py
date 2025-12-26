"""
重试准备节点

当场景时长验证失败时，生成调整建议供下次生成使用。
"""

import logging
from typing import Any, Dict

from app.services.duration_orchestrator.constants import MAX_RETRY_ATTEMPTS
from app.services.duration_orchestrator.state import SceneBudget, SceneStatus
from app.services.duration_orchestrator.utils import compute_adjustment_hint

logger = logging.getLogger(__name__)


def prepare_retry_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    重试准备节点。

    当场景时长验证失败时：
    1. 生成调整建议（增加/删减多少字）
    2. 更新场景状态为待重试
    3. 清空已生成的对白

    输入状态:
        - scene_budgets: 场景预算列表
        - current_scene_index: 当前场景索引
        - generated_dialogues: 已生成的对白

    输出状态更新:
        - scene_budgets: 更新调整建议
        - generated_dialogues: 清空当前场景对白
        - reasoning: 添加重试准备日志
    """
    budgets = state.get("scene_budgets", [])
    current_index = state.get("current_scene_index", 0)

    if current_index >= len(budgets):
        logger.warning("prepare_retry_node: 当前索引越界")
        return {}

    budget: SceneBudget = budgets[current_index]

    # 检查是否达到最大重试次数
    if budget.attempt_count >= MAX_RETRY_ATTEMPTS:
        logger.warning(
            "prepare_retry_node: 场景 %d 达到最大重试次数 %d，强制提交",
            budget.scene_number,
            MAX_RETRY_ATTEMPTS,
        )
        budget.status = SceneStatus.COMMITTED
        budget.last_rejection_reason = "max_retries_exceeded"
        budget.adjustment_hint = None

        reasoning = state.get("reasoning", [])
        reasoning.append(
            f"场景 {budget.scene_number} 达到最大重试次数 ({MAX_RETRY_ATTEMPTS})，强制提交"
        )

        return {
            "scene_budgets": budgets,
            "reasoning": reasoning,
        }

    # 计算调整建议
    actual_duration_ms = int((budget.actual_duration_seconds or 0) * 1000)
    actual_word_count = budget.actual_word_count or 0

    reason, hint = compute_adjustment_hint(
        actual_word_count=actual_word_count,
        actual_duration_ms=actual_duration_ms,
        target_duration_seconds=budget.target_duration_seconds,
    )

    # 更新预算状态
    budget.status = SceneStatus.PENDING
    budget.last_rejection_reason = reason
    budget.adjustment_hint = hint

    logger.info(
        "prepare_retry_node: 场景 %d 准备第 %d 次重试",
        budget.scene_number,
        budget.attempt_count + 1,
        extra={
            "scene_number": budget.scene_number,
            "attempt_count": budget.attempt_count,
            "reason": reason,
            "actual_duration_seconds": budget.actual_duration_seconds,
            "target_duration_seconds": budget.target_duration_seconds,
        },
    )

    # 清空当前场景的已生成对白
    generated_dialogues = state.get("generated_dialogues", {})
    if budget.scene_number in generated_dialogues:
        del generated_dialogues[budget.scene_number]

    reasoning = state.get("reasoning", [])
    reasoning.append(
        f"场景 {budget.scene_number} 准备重试 (第 {budget.attempt_count + 1} 次): {reason}"
    )

    return {
        "scene_budgets": budgets,
        "generated_dialogues": generated_dialogues,
        "reasoning": reasoning,
    }


def should_retry_or_fail(state: Dict[str, Any]) -> str:
    """
    路由函数：判断是否应该重试或标记失败。

    Returns:
        "retry" - 可以重试
        "commit" - 达到最大重试次数，强制提交
    """
    budgets = state.get("scene_budgets", [])
    current_index = state.get("current_scene_index", 0)

    if current_index >= len(budgets):
        return "commit"

    budget: SceneBudget = budgets[current_index]

    if budget.status == SceneStatus.COMMITTED:
        return "commit"

    if budget.attempt_count >= MAX_RETRY_ATTEMPTS:
        return "commit"

    return "retry"
