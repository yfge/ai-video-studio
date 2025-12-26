"""
最终验证节点

验证剧集总时长是否在目标范围内（±10%）。
"""

import logging
from typing import Any, Dict

from app.services.duration_orchestrator.constants import (
    DURATION_TOLERANCE_EPISODE_HIGH,
    DURATION_TOLERANCE_EPISODE_LOW,
)

logger = logging.getLogger(__name__)

# 容差百分比 (10%)
TOLERANCE_PERCENT = (1 - DURATION_TOLERANCE_EPISODE_LOW) * 100


def final_validation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    最终验证节点。

    验证剧集总时长是否在目标容差范围内（默认 ±10%）。

    输入状态:
        - statistics: 统计信息（包含 total_actual_duration_seconds）
        - total_duration_minutes: 目标总时长（分钟）

    输出状态更新:
        - final_validation_result: 验证结果
        - success: 是否验证通过
        - reasoning: 添加验证日志
    """
    statistics = state.get("statistics", {})
    total_duration_minutes = state.get("total_duration_minutes", 0)
    episode_id = state.get("episode_id")

    reasoning = state.get("reasoning", [])
    errors = state.get("errors", [])

    # 获取实际和目标时长
    total_actual = statistics.get("total_actual_duration_seconds", 0)
    total_target = total_duration_minutes * 60

    # 计算时长比例
    ratio = total_actual / total_target if total_target > 0 else 0

    # 计算容差范围 (使用常量定义的 LOW/HIGH)
    min_ratio = DURATION_TOLERANCE_EPISODE_LOW
    max_ratio = DURATION_TOLERANCE_EPISODE_HIGH

    # 判断是否在容差内
    is_within_tolerance = min_ratio <= ratio <= max_ratio

    # 计算偏差
    deviation_seconds = total_actual - total_target
    deviation_percent = (ratio - 1) * 100

    logger.info(
        "final_validation_node: 最终验证",
        extra={
            "episode_id": episode_id,
            "total_actual": total_actual,
            "total_target": total_target,
            "ratio": ratio,
            "min_ratio": min_ratio,
            "max_ratio": max_ratio,
            "is_within_tolerance": is_within_tolerance,
            "deviation_seconds": deviation_seconds,
            "deviation_percent": deviation_percent,
        },
    )

    # 构建验证结果
    validation_result = {
        "passed": is_within_tolerance,
        "total_actual_duration_seconds": round(total_actual, 2),
        "total_target_duration_seconds": total_target,
        "duration_ratio": round(ratio, 4),
        "deviation_seconds": round(deviation_seconds, 2),
        "deviation_percent": round(deviation_percent, 2),
        "tolerance_percent": TOLERANCE_PERCENT,
        "tolerance_range": {
            "min_seconds": round(total_target * min_ratio, 2),
            "max_seconds": round(total_target * max_ratio, 2),
        },
    }

    # 生成验证日志
    if is_within_tolerance:
        reasoning.append(
            f"最终验证通过: 总时长 {total_actual:.1f}s / {total_target}s "
            f"({ratio:.1%}), 在 ±{TOLERANCE_PERCENT:.0f}% 容差内"
        )
    else:
        direction = "过长" if ratio > 1 else "过短"
        reasoning.append(
            f"最终验证失败: 总时长 {total_actual:.1f}s / {total_target}s "
            f"({ratio:.1%}), {direction} {abs(deviation_percent):.1f}%, "
            f"超出 ±{TOLERANCE_PERCENT:.0f}% 容差"
        )
        errors.append(
            f"Episode {episode_id} 总时长验证失败: "
            f"{direction} {abs(deviation_percent):.1f}%"
        )

    return {
        "final_validation_result": validation_result,
        "success": is_within_tolerance,
        "reasoning": reasoning,
        "errors": errors,
        "phase": "validated",
    }


def should_pass_or_fail(state: Dict[str, Any]) -> str:
    """
    路由函数：判断最终验证是否通过。

    Returns:
        "pass" - 验证通过
        "fail" - 验证失败
    """
    validation_result = state.get("final_validation_result", {})
    return "pass" if validation_result.get("passed", False) else "fail"
