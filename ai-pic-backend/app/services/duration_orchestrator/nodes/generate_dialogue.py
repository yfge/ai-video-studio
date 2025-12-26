"""
对白生成节点

根据场景预算调用 ScriptLangGraphAgent 生成对白。
"""

import logging
from typing import Any, Dict

from app.services.duration_orchestrator.state import SceneBudget, SceneStatus
from app.services.duration_orchestrator.utils import count_dialogue_words

logger = logging.getLogger(__name__)


async def generate_dialogue_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    对白生成节点。

    根据当前场景的预算约束，调用 ScriptLangGraphAgent 生成对白。

    输入状态:
        - scene_budgets: 场景预算列表
        - current_scene_index: 当前场景索引
        - script_agent: ScriptLangGraphAgent 实例
        - episode: Episode 数据
        - story: Story 数据
        - generation_config: 生成配置

    输出状态更新:
        - scene_budgets: 更新生成结果
        - generated_dialogues: 添加生成的对白
        - reasoning: 添加生成日志
    """
    budgets = state.get("scene_budgets", [])
    current_index = state.get("current_scene_index", 0)

    if current_index >= len(budgets):
        logger.warning("generate_dialogue_node: 当前索引越界")
        return {}

    budget: SceneBudget = budgets[current_index]
    script_agent = state.get("script_agent")
    episode = state.get("episode", {})
    story = state.get("story", {})
    generation_config = state.get("generation_config", {})

    if not script_agent:
        logger.error("generate_dialogue_node: 缺少 script_agent")
        return {
            "errors": state.get("errors", []) + ["missing_script_agent"],
        }

    # 更新状态为进行中
    budget.status = SceneStatus.IN_PROGRESS
    budget.attempt_count += 1

    logger.info(
        "generate_dialogue_node: 开始生成场景 %d 的对白",
        budget.scene_number,
        extra={
            "scene_number": budget.scene_number,
            "target_duration": budget.target_duration_seconds,
            "target_word_count": budget.target_word_count,
            "attempt": budget.attempt_count,
        },
    )

    # 准备场景预算列表（只包含当前场景）
    # 这样 Script Agent 可以为当前场景生成符合字数要求的对白
    current_budgets = [budget]

    try:
        # 调用 ScriptLangGraphAgent
        result = await script_agent.generate(
            episode=episode,
            story=story,
            format_type=generation_config.get("format_type", "short_video"),
            language=generation_config.get("language", "zh"),
            dialogue_style=generation_config.get("dialogue_style", "natural"),
            scene_detail_level=generation_config.get("scene_detail_level", "detailed"),
            additional_requirements=generation_config.get("additional_requirements"),
            style_preferences=generation_config.get("style_preferences"),
            model=generation_config.get("model"),
            prefer_provider=generation_config.get("prefer_provider"),
            temperature=generation_config.get("temperature", 0.7),
            scene_budgets=current_budgets,
        )

        if not result or "error" in result:
            error_msg = result.get("error", "unknown_error") if result else "no_result"
            logger.warning(
                "generate_dialogue_node: 场景 %d 生成失败: %s",
                budget.scene_number,
                error_msg,
            )
            budget.status = SceneStatus.PENDING
            return {
                "scene_budgets": budgets,
                "errors": state.get("errors", [])
                + [f"scene_{budget.scene_number}_generation_failed: {error_msg}"],
            }

        # 提取生成的对白
        content = result.get("content", {})
        dialogues = content.get("dialogues", []) if isinstance(content, dict) else []

        # 过滤出当前场景的对白
        scene_dialogues = [
            d for d in dialogues if d.get("scene_number") == budget.scene_number
        ]

        # 计算实际字数
        actual_word_count = count_dialogue_words(scene_dialogues)
        budget.actual_word_count = actual_word_count

        logger.info(
            "generate_dialogue_node: 场景 %d 对白生成完成",
            budget.scene_number,
            extra={
                "scene_number": budget.scene_number,
                "dialogue_count": len(scene_dialogues),
                "actual_word_count": actual_word_count,
                "target_word_count": budget.target_word_count,
            },
        )

        # 更新已生成的对白
        generated_dialogues = state.get("generated_dialogues", {})
        generated_dialogues[budget.scene_number] = scene_dialogues

        reasoning = state.get("reasoning", [])
        reasoning.append(
            f"场景 {budget.scene_number} 对白生成完成: "
            f"{len(scene_dialogues)} 条对白，"
            f"{actual_word_count} 字 (目标 {budget.target_word_count} 字)"
        )

        return {
            "scene_budgets": budgets,
            "generated_dialogues": generated_dialogues,
            "reasoning": reasoning,
            "last_generation_result": result,
        }

    except Exception as exc:
        logger.exception(
            "generate_dialogue_node: 场景 %d 生成异常",
            budget.scene_number,
        )
        budget.status = SceneStatus.PENDING
        return {
            "scene_budgets": budgets,
            "errors": state.get("errors", [])
            + [f"scene_{budget.scene_number}_exception: {str(exc)}"],
        }


def should_proceed_to_tts(state: Dict[str, Any]) -> str:
    """
    路由函数：判断是否应该进入 TTS 试跑阶段。

    Returns:
        "tts" - 有对白，进入 TTS 阶段
        "retry" - 无对白或失败，重试
        "failed" - 达到最大重试次数
    """
    from app.services.duration_orchestrator.constants import MAX_RETRY_ATTEMPTS

    budgets = state.get("scene_budgets", [])
    current_index = state.get("current_scene_index", 0)

    if current_index >= len(budgets):
        return "failed"

    budget: SceneBudget = budgets[current_index]
    generated_dialogues = state.get("generated_dialogues", {})
    scene_dialogues = generated_dialogues.get(budget.scene_number, [])

    if not scene_dialogues:
        if budget.attempt_count >= MAX_RETRY_ATTEMPTS:
            return "failed"
        return "retry"

    return "tts"
