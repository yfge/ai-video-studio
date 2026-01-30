"""
场景提交节点

验证通过后提交场景，并触发后续场景的预算再平衡。
"""

from typing import Any, Dict

from app.core.logging import get_logger
from app.services.duration_orchestrator.state import SceneBudget, SceneStatus
from app.services.duration_orchestrator.utils import rebalance_remaining_budgets

logger = get_logger()


def commit_scene_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    场景提交节点。

    将当前场景标记为已提交，并触发后续场景的预算再平衡。

    输入状态:
        - scene_budgets: 场景预算列表
        - current_scene_index: 当前场景索引
        - generated_dialogues: 已生成的对白

    输出状态更新:
        - scene_budgets: 更新状态和后续场景预算
        - committed_scenes: 添加已提交场景数据
        - current_scene_index: 移动到下一个场景
        - reasoning: 添加提交日志
    """
    budgets = state.get("scene_budgets", [])
    current_index = state.get("current_scene_index", 0)

    if current_index >= len(budgets):
        logger.warning("commit_scene_node: 当前索引越界")
        return {}

    budget: SceneBudget = budgets[current_index]
    generated_dialogues = state.get("generated_dialogues", {})
    scene_dialogues = generated_dialogues.get(budget.scene_number, [])

    # 标记为已提交
    budget.status = SceneStatus.COMMITTED

    # 计算时长偏差
    actual_seconds = budget.actual_duration_seconds or 0
    target_seconds = budget.target_duration_seconds
    deviation_seconds = actual_seconds - target_seconds

    logger.info(
        "commit_scene_node: 场景 %d 已提交",
        budget.scene_number,
        extra={
            "event": "scene_committed",
            "episode_id": state.get("episode_id"),
            "scene_number": budget.scene_number,
            "actual_duration_seconds": actual_seconds,
            "target_duration_seconds": target_seconds,
            "deviation_seconds": deviation_seconds,
            "deviation_ratio": round(deviation_seconds / target_seconds, 3)
            if target_seconds > 0
            else 0,
            "attempt_count": budget.attempt_count,
        },
    )

    # 触发预算再平衡（如果有偏差且还有后续场景）
    if deviation_seconds != 0 and current_index < len(budgets) - 1:
        rebalance_remaining_budgets(
            budgets=budgets,
            current_index=current_index,
            actual_duration=actual_seconds,
        )
        logger.info(
            "commit_scene_node: 已触发预算再平衡",
            extra={
                "event": "budget_rebalanced",
                "episode_id": state.get("episode_id"),
                "scene_number": budget.scene_number,
                "deviation_seconds": deviation_seconds,
                "remaining_scenes": len(budgets) - current_index - 1,
            },
        )

    # 保存已提交的场景数据
    committed_scenes = state.get("committed_scenes", {})
    committed_scenes[budget.scene_number] = {
        "scene_number": budget.scene_number,
        "dialogues": scene_dialogues,
        "target_duration_seconds": target_seconds,
        "actual_duration_seconds": actual_seconds,
        "deviation_seconds": deviation_seconds,
        "attempt_count": budget.attempt_count,
    }

    # 移动到下一个场景
    next_index = current_index + 1

    reasoning = state.get("reasoning", [])
    reasoning.append(
        f"场景 {budget.scene_number} 已提交: "
        f"{actual_seconds:.1f}s (目标 {target_seconds}s, "
        f"偏差 {deviation_seconds:+.1f}s, "
        f"尝试 {budget.attempt_count} 次)"
    )

    return {
        "scene_budgets": budgets,
        "committed_scenes": committed_scenes,
        "current_scene_index": next_index,
        "reasoning": reasoning,
    }


def should_continue_or_assemble(state: Dict[str, Any]) -> str:
    """
    路由函数：判断是否继续处理下一个场景或进入组装阶段。

    Returns:
        "continue" - 还有待处理的场景
        "assemble" - 所有场景已处理，进入组装阶段
    """
    budgets = state.get("scene_budgets", [])
    current_index = state.get("current_scene_index", 0)

    if current_index >= len(budgets):
        return "assemble"

    # 检查是否还有待处理的场景
    remaining_pending = [
        b for b in budgets[current_index:] if b.status == SceneStatus.PENDING
    ]

    if remaining_pending:
        return "continue"

    return "assemble"
