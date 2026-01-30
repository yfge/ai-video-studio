"""
预算分配节点

根据剧集总时长和场景数量，分配每个场景的时长预算和字数目标。
"""

import logging
from typing import Any, Dict

from app.services.duration_orchestrator.utils import (
    allocate_scene_budgets,
    format_budget_summary,
)

logger = logging.getLogger(__name__)


def allocate_budget_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    预算分配节点。

    根据 total_duration_minutes 和 scenes_from_episode 计算每个场景的时长预算。

    输入状态:
        - total_duration_minutes: 剧集总时长（分钟）
        - scenes_from_episode: Episode Agent 产出的场景列表

    输出状态更新:
        - scene_budgets: 场景预算列表
        - buffer_seconds: 预留 buffer 秒数
        - remaining_budget_seconds: 剩余可分配秒数
        - phase: 更新为 "generating"
        - reasoning: 添加分配日志
    """
    total_duration_minutes = state.get("total_duration_minutes", 0)
    scenes = state.get("scenes_from_episode", [])

    logger.info(
        "allocate_budget_node: 开始分配预算",
        extra={
            "episode_id": state.get("episode_id"),
            "total_duration_minutes": total_duration_minutes,
            "scene_count": len(scenes),
        },
    )

    if not scenes:
        error_msg = "无场景可分配，请先生成剧集场景"
        logger.error(error_msg)
        return {
            "phase": "failed",
            "errors": state.get("errors", []) + [error_msg],
        }

    # 分配预算
    budgets, buffer_seconds = allocate_scene_budgets(
        total_duration_minutes=total_duration_minutes,
        scenes=scenes,
    )

    # 计算剩余可分配秒数
    total_allocated = sum(b.target_duration_seconds for b in budgets)
    remaining = total_duration_minutes * 60 - buffer_seconds - total_allocated

    # 生成分配摘要
    summary = format_budget_summary(budgets)
    logger.info(f"allocate_budget_node: 分配完成\n{summary}")

    reasoning = state.get("reasoning", [])
    reasoning.append(
        f"预算分配完成: {len(budgets)} 个场景，"
        f"总目标 {total_allocated}s，"
        f"buffer {buffer_seconds}s"
    )

    return {
        "scene_budgets": budgets,
        "buffer_seconds": buffer_seconds,
        "remaining_budget_seconds": remaining,
        "phase": "generating",
        "current_scene_index": 0,
        "reasoning": reasoning,
    }


def should_proceed_to_generation(state: Dict[str, Any]) -> str:
    """
    路由函数：判断是否应该进入生成阶段。

    Returns:
        "generate" - 有待处理的场景，进入生成阶段
        "assemble" - 所有场景已处理，进入组装阶段
        "failed" - 发生错误
    """
    phase = state.get("phase", "")

    if phase == "failed":
        return "failed"

    budgets = state.get("scene_budgets", [])
    if not budgets:
        return "failed"

    # 检查是否有待处理的场景
    from app.services.duration_orchestrator.state import SceneStatus

    pending = [b for b in budgets if b.status == SceneStatus.PENDING]

    if pending:
        return "generate"
    else:
        return "assemble"
