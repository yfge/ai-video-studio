"""
TTS 试跑节点

调用 TTS 服务获取对白的实际时长，用于验证场景时长是否达标。
"""

import logging
from typing import Any, Dict, List

from app.services.duration_orchestrator.constants import WORDS_PER_SECOND
from app.services.duration_orchestrator.state import SceneBudget
from app.services.duration_orchestrator.utils import count_dialogue_words

logger = logging.getLogger(__name__)


def estimate_duration_from_dialogues(
    dialogues: List[Dict[str, Any]],
    speaking_rate: float = WORDS_PER_SECOND,
) -> int:
    """
    根据对白字数估算时长（毫秒）。

    这是快速估算模式，不调用实际 TTS。
    用于快速验证对白字数是否在目标范围内。

    Args:
        dialogues: 对白列表，每个元素包含 content 字段
        speaking_rate: 每秒汉字数（默认 4.7，来自线上 TTS 语速校准）

    Returns:
        估算时长（毫秒）
    """
    word_count = count_dialogue_words(dialogues)
    duration_seconds = word_count / speaking_rate
    return int(duration_seconds * 1000)


async def tts_trial_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    TTS 试跑节点。

    获取场景对白的实际或估算时长。

    支持两种模式：
    1. 估算模式（默认）：根据字数快速估算，无需调用 TTS
    2. 实际模式：调用 TTS 服务获取真实时长

    输入状态:
        - scene_budgets: 场景预算列表
        - current_scene_index: 当前场景索引
        - generated_dialogues: 已生成的对白
        - use_actual_tts: 是否使用实际 TTS（默认 False）
        - tts_service: TTS 服务实例（实际模式需要）

    输出状态更新:
        - scene_budgets: 更新实际时长
        - reasoning: 添加试跑日志
    """
    budgets = state.get("scene_budgets", [])
    current_index = state.get("current_scene_index", 0)
    use_actual_tts = state.get("use_actual_tts", False)

    if current_index >= len(budgets):
        logger.warning("tts_trial_node: 当前索引越界")
        return {}

    budget: SceneBudget = budgets[current_index]
    generated_dialogues = state.get("generated_dialogues", {})
    scene_dialogues = generated_dialogues.get(budget.scene_number, [])

    if not scene_dialogues:
        logger.warning(
            "tts_trial_node: 场景 %d 无对白数据",
            budget.scene_number,
        )
        return {}

    reasoning = state.get("reasoning", [])

    if use_actual_tts:
        # 实际 TTS 模式
        actual_duration_ms = await _run_actual_tts(
            state=state,
            dialogues=scene_dialogues,
            budget=budget,
        )
    else:
        # 估算模式
        actual_duration_ms = estimate_duration_from_dialogues(scene_dialogues)

    # 转换为秒
    actual_duration_seconds = actual_duration_ms / 1000.0
    budget.actual_duration_seconds = actual_duration_seconds

    # 计算偏差
    target_seconds = budget.target_duration_seconds
    deviation = actual_duration_seconds - target_seconds
    deviation_percent = (deviation / target_seconds * 100) if target_seconds > 0 else 0

    mode_label = "TTS实测" if use_actual_tts else "字数估算"
    logger.info(
        "tts_trial_node: 场景 %d %s完成",
        budget.scene_number,
        mode_label,
        extra={
            "scene_number": budget.scene_number,
            "mode": "actual" if use_actual_tts else "estimate",
            "actual_duration_seconds": actual_duration_seconds,
            "target_duration_seconds": target_seconds,
            "deviation_seconds": deviation,
            "deviation_percent": deviation_percent,
        },
    )

    reasoning.append(
        f"场景 {budget.scene_number} {mode_label}: "
        f"{actual_duration_seconds:.1f}s (目标 {target_seconds}s, "
        f"偏差 {deviation:+.1f}s / {deviation_percent:+.0f}%)"
    )

    return {
        "scene_budgets": budgets,
        "reasoning": reasoning,
    }


async def _run_actual_tts(
    state: Dict[str, Any],
    dialogues: List[Dict[str, Any]],
    budget: SceneBudget,
) -> int:
    """
    调用实际 TTS 服务获取时长。

    使用采样策略：如果对白超过 5 条，采样 3 条计算平均语速。

    Args:
        state: 状态字典
        dialogues: 对白列表
        budget: 场景预算

    Returns:
        估算的总时长（毫秒）
    """
    tts_service = state.get("tts_service")
    voice_config = state.get("voice_config", {})

    if not tts_service:
        logger.warning("tts_trial_node: 无 TTS 服务，降级为估算模式")
        return estimate_duration_from_dialogues(dialogues)

    # 采样策略：超过 5 条对白时采样 3 条
    sample_size = 3
    if len(dialogues) <= sample_size:
        sample_dialogues = dialogues
    else:
        # 采样首、中、尾
        mid_index = len(dialogues) // 2
        sample_dialogues = [
            dialogues[0],
            dialogues[mid_index],
            dialogues[-1],
        ]

    total_sample_chars = 0
    total_sample_duration_ms = 0

    try:
        for dlg in sample_dialogues:
            content = dlg.get("content", "")
            if not content:
                continue

            # 调用 TTS 获取时长
            result = await tts_service.generate_speech(
                text=content,
                voice_type=voice_config.get("voice_type"),
                speed=voice_config.get("speed", 1.0),
                prefer_provider=voice_config.get("provider"),
            )

            if result and result.get("duration"):
                duration_ms = int(result["duration"] * 1000)
                total_sample_chars += len(content)
                total_sample_duration_ms += duration_ms

        if total_sample_chars > 0 and total_sample_duration_ms > 0:
            # 计算实际语速
            actual_chars_per_second = total_sample_chars / (
                total_sample_duration_ms / 1000
            )

            # 用实际语速估算总时长
            total_chars = count_dialogue_words(dialogues)
            estimated_total_ms = int(total_chars / actual_chars_per_second * 1000)

            logger.info(
                "tts_trial_node: 采样 TTS 完成",
                extra={
                    "scene_number": budget.scene_number,
                    "sample_count": len(sample_dialogues),
                    "actual_chars_per_second": actual_chars_per_second,
                    "total_chars": total_chars,
                    "estimated_total_ms": estimated_total_ms,
                },
            )
            return estimated_total_ms

    except Exception as exc:
        logger.warning(
            "tts_trial_node: TTS 采样失败，降级为估算模式: %s",
            exc,
        )

    # 降级为估算模式
    return estimate_duration_from_dialogues(dialogues)
