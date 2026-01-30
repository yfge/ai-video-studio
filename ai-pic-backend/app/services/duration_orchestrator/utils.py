"""
Duration Orchestrator 工具函数

提供预算分配、字数计算、调整建议生成等工具函数。
"""

import logging
from typing import Any, Dict, List, Tuple

from app.services.duration_orchestrator.constants import (
    ADJUSTMENT_WORDS_PER_DIALOGUE,
    BUFFER_RATIO,
    DEFAULT_SCENE_DURATION_SECONDS,
    DIALOGUE_DENSITY_FACTOR,
    DURATION_TOLERANCE_SCENE_HIGH,
    DURATION_TOLERANCE_SCENE_LOW,
    MAX_SCENE_DURATION_SECONDS,
    MIN_SCENE_DURATION_SECONDS,
    MIN_WORD_ADJUSTMENT,
    MIN_WORD_REDUCTION,
    WORDS_PER_SECOND,
)
from app.services.duration_orchestrator.state import SceneBudget, SceneStatus

logger = logging.getLogger(__name__)


def calculate_target_word_count(duration_seconds: int) -> int:
    """
    根据目标时长计算目标对白字数。

    考虑因素:
    - DIALOGUE_DENSITY_FACTOR (0.90): 不是所有时间都在说话，需要考虑
      停顿、语气词、情绪表达、角色反应时间、环境音等
    - WORDS_PER_SECOND (4.7): 校准后的中文 TTS 语速

    例如: 60秒场景
    - 实际对白时间: 60 * 0.90 = 54秒
    - 目标字数: 54 * 4.7 ≈ 254字

    Args:
        duration_seconds: 目标时长 (秒)

    Returns:
        目标对白字数
    """
    effective_seconds = duration_seconds * DIALOGUE_DENSITY_FACTOR
    return int(effective_seconds * WORDS_PER_SECOND)


def allocate_scene_budgets(
    total_duration_minutes: int,
    scenes: List[Dict[str, Any]],
    buffer_ratio: float = BUFFER_RATIO,
) -> Tuple[List[SceneBudget], int]:
    """
    分配每个场景的时长预算。

    策略:
    1. 保留 buffer_ratio (默认 5%) 用于场景间过渡
    2. 如果场景有 estimated_duration_seconds，按比例缩放
    3. 否则平均分配

    Args:
        total_duration_minutes: 总时长 (分钟)
        scenes: 场景列表 (来自 Episode Agent)
        buffer_ratio: 预留 buffer 比例

    Returns:
        (场景预算列表, buffer 秒数)
    """
    if not scenes:
        logger.warning("allocate_scene_budgets: 无场景可分配")
        return [], 0

    total_seconds = total_duration_minutes * 60
    buffer_seconds = int(total_seconds * buffer_ratio)
    available_seconds = total_seconds - buffer_seconds

    # 检查是否有估算时长
    has_estimates = any(s.get("estimated_duration_seconds") for s in scenes)

    budgets: List[SceneBudget] = []

    if has_estimates:
        # 按估算时长比例分配
        total_estimated = sum(
            s.get("estimated_duration_seconds", DEFAULT_SCENE_DURATION_SECONDS)
            for s in scenes
        )

        for idx, scene in enumerate(scenes):
            estimated = scene.get(
                "estimated_duration_seconds", DEFAULT_SCENE_DURATION_SECONDS
            )
            ratio = (
                estimated / total_estimated if total_estimated > 0 else 1 / len(scenes)
            )
            target = int(available_seconds * ratio)

            # 确保在合理范围内
            target = max(
                MIN_SCENE_DURATION_SECONDS, min(target, MAX_SCENE_DURATION_SECONDS)
            )

            budgets.append(
                SceneBudget(
                    scene_number=scene.get("scene_number", idx + 1),
                    scene_index=idx,
                    target_duration_seconds=target,
                    target_word_count=calculate_target_word_count(target),
                    min_duration_seconds=int(target * DURATION_TOLERANCE_SCENE_LOW),
                    max_duration_seconds=int(target * DURATION_TOLERANCE_SCENE_HIGH),
                )
            )
    else:
        # 平均分配
        per_scene = available_seconds // len(scenes)
        per_scene = max(
            MIN_SCENE_DURATION_SECONDS, min(per_scene, MAX_SCENE_DURATION_SECONDS)
        )

        for idx, scene in enumerate(scenes):
            budgets.append(
                SceneBudget(
                    scene_number=scene.get("scene_number", idx + 1),
                    scene_index=idx,
                    target_duration_seconds=per_scene,
                    target_word_count=calculate_target_word_count(per_scene),
                    min_duration_seconds=int(per_scene * DURATION_TOLERANCE_SCENE_LOW),
                    max_duration_seconds=int(per_scene * DURATION_TOLERANCE_SCENE_HIGH),
                )
            )

    logger.info(
        "allocate_scene_budgets: 分配完成",
        extra={
            "total_duration_minutes": total_duration_minutes,
            "scene_count": len(scenes),
            "buffer_seconds": buffer_seconds,
            "available_seconds": available_seconds,
            "has_estimates": has_estimates,
        },
    )

    return budgets, buffer_seconds


def compute_adjustment_hint(
    actual_word_count: int,
    actual_duration_ms: int,
    target_duration_seconds: int,
) -> Tuple[str, str]:
    """
    计算调整建议。

    根据实际时长与目标时长的差异，生成具体的调整建议。

    Args:
        actual_word_count: 实际对白字数
        actual_duration_ms: 实际 TTS 时长 (毫秒)
        target_duration_seconds: 目标时长 (秒)

    Returns:
        (rejection_reason, adjustment_hint)
    """
    target_ms = target_duration_seconds * 1000
    diff_ms = target_ms - actual_duration_ms
    diff_seconds = abs(diff_ms) / 1000

    # 估算需要增减的字数（按当前基准语速）
    words_per_second = WORDS_PER_SECOND
    word_diff = max(int(abs(diff_seconds) * words_per_second), MIN_WORD_ADJUSTMENT)

    # 估算需要增减的对白句数
    dialogue_diff = max(1, word_diff // ADJUSTMENT_WORDS_PER_DIALOGUE)

    if diff_ms > 0:
        # 时长不足
        reason = "duration_too_short"
        hint = (
            f"当前对白时长 {actual_duration_ms / 1000:.1f} 秒，"
            f"目标 {target_duration_seconds} 秒，"
            f"差距 {diff_seconds:.1f} 秒。\n"
            f"建议增加约 {word_diff} 字的对白（约 {dialogue_diff} 句）。\n"
            f"可以：\n"
            f"1. 扩展现有对白的情感描写和反应\n"
            f"2. 增加角色间的互动和追问\n"
            f"3. 添加内心独白或旁白\n"
            f"4. 丰富场景细节描述"
        )
    else:
        # 时长过长
        word_diff = max(word_diff, MIN_WORD_REDUCTION)
        dialogue_diff = max(1, word_diff // ADJUSTMENT_WORDS_PER_DIALOGUE)
        reason = "duration_too_long"
        hint = (
            f"当前对白时长 {actual_duration_ms / 1000:.1f} 秒，"
            f"目标 {target_duration_seconds} 秒，"
            f"超出 {diff_seconds:.1f} 秒。\n"
            f"建议删减约 {word_diff} 字的对白（约 {dialogue_diff} 句）。\n"
            f"可以：\n"
            f"1. 精简冗余对白，保留核心信息\n"
            f"2. 合并相似内容的对话\n"
            f"3. 删除对情节推进贡献不大的台词\n"
            f"4. 简化过长的描述性语句"
        )

    return reason, hint


def count_dialogue_words(dialogues: List[Dict[str, Any]]) -> int:
    """
    统计对白总字数。

    Args:
        dialogues: 对白列表

    Returns:
        总字数
    """
    total = 0
    for dlg in dialogues:
        content = dlg.get("content", "")
        if isinstance(content, str):
            total += len(content)
    return total


def estimate_duration_from_words(word_count: int) -> int:
    """
    根据字数估算时长 (秒)。

    Args:
        word_count: 字数

    Returns:
        估算时长 (秒)
    """
    return int(word_count / WORDS_PER_SECOND)


def rebalance_remaining_budgets(
    budgets: List[SceneBudget],
    current_index: int,
    actual_duration: float,
) -> None:
    """
    根据实际时长调整后续场景的预算。

    如果当前场景超时/欠时，从后续场景预算中调整。

    Args:
        budgets: 场景预算列表 (会被原地修改)
        current_index: 当前场景索引
        actual_duration: 当前场景实际时长 (秒)
    """
    if current_index >= len(budgets) - 1:
        # 已是最后一个场景，无需调整
        return

    current_budget = budgets[current_index]
    diff = actual_duration - current_budget.target_duration_seconds

    if abs(diff) < 5:
        # 差异太小，不调整
        return

    # 计算后续待处理场景
    remaining_budgets = [
        b for b in budgets[current_index + 1 :] if b.status == SceneStatus.PENDING
    ]

    if not remaining_budgets:
        return

    # 将差异平均分配到后续场景
    adjustment_per_scene = -diff / len(remaining_budgets)

    for budget in remaining_budgets:
        new_target = int(budget.target_duration_seconds + adjustment_per_scene)
        # 确保在合理范围内
        new_target = max(
            MIN_SCENE_DURATION_SECONDS, min(new_target, MAX_SCENE_DURATION_SECONDS)
        )
        budget.target_duration_seconds = new_target
        budget.target_word_count = calculate_target_word_count(new_target)
        budget.min_duration_seconds = int(new_target * DURATION_TOLERANCE_SCENE_LOW)
        budget.max_duration_seconds = int(new_target * DURATION_TOLERANCE_SCENE_HIGH)

    logger.info(
        "rebalance_remaining_budgets: 预算再平衡",
        extra={
            "current_scene": current_budget.scene_number,
            "diff_seconds": diff,
            "remaining_scenes": len(remaining_budgets),
            "adjustment_per_scene": adjustment_per_scene,
        },
    )


def format_budget_summary(budgets: List[SceneBudget]) -> str:
    """
    格式化预算摘要，用于日志和调试。

    Args:
        budgets: 场景预算列表

    Returns:
        格式化的摘要字符串
    """
    lines = ["场景预算摘要:"]
    for b in budgets:
        status_icon = {
            SceneStatus.PENDING: "⏳",
            SceneStatus.IN_PROGRESS: "🔄",
            SceneStatus.COMMITTED: "✅",
            SceneStatus.FAILED: "❌",
        }.get(b.status, "?")

        actual_info = ""
        if b.actual_duration_seconds is not None:
            ratio = b.duration_ratio()
            actual_info = f" -> 实际: {b.actual_duration_seconds:.1f}s ({ratio:.0%})"

        lines.append(
            f"  {status_icon} 场景{b.scene_number}: "
            f"目标 {b.target_duration_seconds}s, "
            f"字数 {b.target_word_count}, "
            f"尝试 {b.attempt_count}次"
            f"{actual_info}"
        )

    return "\n".join(lines)
