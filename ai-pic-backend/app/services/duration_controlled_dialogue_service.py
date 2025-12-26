"""
时长精控对白生成服务

使用 Duration Orchestrator Agent 实现端到端时长闭环验证。
"""

import logging
from typing import Any, Dict, List, Optional

from app.models.script import Episode, Script, Story
from app.services.duration_orchestrator.agent import DurationOrchestratorAgent
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def _scene_to_dict(scene) -> Dict[str, Any]:
    """将 Scene ORM 对象转换为字典。"""
    return {
        "scene_number": getattr(scene, "scene_number", None),
        "id": getattr(scene, "id", None),
        "title": getattr(scene, "title", None),
        "summary": getattr(scene, "summary", None),
        "location": getattr(scene, "location", None),
        "time_of_day": getattr(scene, "time_of_day", None),
        "characters": getattr(scene, "characters", None) or [],
        "estimated_duration_seconds": getattr(
            scene, "estimated_duration_seconds", None
        ),
    }


def _episode_to_dict(episode: Episode) -> Dict[str, Any]:
    """将 Episode ORM 对象转换为字典。"""
    return {
        "id": episode.id,
        "title": getattr(episode, "title", None),
        "episode_number": getattr(episode, "episode_number", None),
        "duration_minutes": getattr(episode, "duration_minutes", None),
    }


def _story_to_dict(story: Story) -> Dict[str, Any]:
    """将 Story ORM 对象转换为字典。"""
    return {
        "id": story.id,
        "title": getattr(story, "title", None),
        "genre": getattr(story, "genre", None),
        "virtual_ip_id": getattr(story, "virtual_ip_id", None),
    }


async def generate_dialogue_with_duration_control(
    db: Session,
    *,
    story: Story,
    episode: Episode,
    script: Script,
    scenes: List,
    tts_model: str = "speech-2.6-hd",
    use_actual_tts: bool = False,
    generation_config: Optional[Dict[str, Any]] = None,
    voice_config: Optional[Dict[str, Any]] = None,
    progress_callback: Optional[callable] = None,
) -> Dict[str, Any]:
    """
    使用 Duration Orchestrator 生成时长精控对白。

    Args:
        db: 数据库会话
        story: Story 对象
        episode: Episode 对象
        script: Script 对象
        scenes: Scene 对象列表
        tts_model: TTS 模型
        use_actual_tts: 是否使用实际 TTS 测量（否则使用字数估算）
        generation_config: 对白生成配置
        voice_config: TTS 语音配置
        progress_callback: 进度回调函数

    Returns:
        Duration Orchestrator 结果字典
    """
    logger.info(
        "generate_dialogue_with_duration_control: 开始时长精控对白生成",
        extra={
            "episode_id": episode.id,
            "script_id": script.id,
            "scene_count": len(scenes),
            "tts_model": tts_model,
            "use_actual_tts": use_actual_tts,
        },
    )

    # 转换场景为字典格式
    scenes_data = [_scene_to_dict(s) for s in scenes]

    # 获取目标时长（分钟）
    total_duration_minutes = getattr(episode, "duration_minutes", None) or 3

    # 构建 TTS 服务配置
    voice_cfg = voice_config or {}
    voice_cfg["tts_model"] = tts_model

    # 创建 Duration Orchestrator
    agent = DurationOrchestratorAgent(
        script_agent=None,  # 目前不集成 ScriptLangGraphAgent
        tts_service=None,  # 目前使用字数估算
        use_actual_tts=use_actual_tts,
    )

    # 执行编排
    result = await agent.orchestrate(
        episode_id=episode.id,
        script_id=script.id,
        story_id=story.id,
        total_duration_minutes=total_duration_minutes,
        scenes=scenes_data,
        episode=_episode_to_dict(episode),
        story=_story_to_dict(story),
        generation_config=generation_config,
        voice_config=voice_cfg,
    )

    # 记录结果
    success = result.get("success", False)
    statistics = result.get("statistics", {})
    final_validation = result.get("final_validation", {})

    logger.info(
        "generate_dialogue_with_duration_control: 时长精控对白生成完成",
        extra={
            "episode_id": episode.id,
            "success": success,
            "total_actual_duration": statistics.get("total_actual_duration_seconds", 0),
            "total_target_duration": statistics.get("total_target_duration_seconds", 0),
            "duration_ratio": statistics.get("duration_ratio", 0),
            "final_validation_passed": final_validation.get("passed"),
        },
    )

    return result


async def persist_orchestrator_results(
    db: Session,
    *,
    script: Script,
    result: Dict[str, Any],
) -> None:
    """
    将 Duration Orchestrator 结果持久化到数据库。

    注意：这是一个占位函数，待后续实现与现有 Scene/SceneBeat 模型的集成。

    Args:
        db: 数据库会话
        script: Script 对象
        result: Duration Orchestrator 结果
    """
    # TODO: 实现结果持久化
    # 1. 更新 Scene 的 estimated_duration_seconds
    # 2. 创建/更新 SceneBeat 记录
    # 3. 更新 Script 的对白时间轴数据
    logger.info(
        "persist_orchestrator_results: 持久化结果（待实现）",
        extra={
            "script_id": script.id,
            "scene_count": len(result.get("committed_scenes", {})),
        },
    )
