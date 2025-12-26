"""
时长精控对白生成服务

混合模式：使用 Duration Orchestrator 进行预算分配和验证，
使用现有 dialogue_audio_service 进行实际 TTS 生成。
"""

import logging
from typing import Any, Dict, List, Optional

from app.models.script import Episode, Script, Story
from app.models.story_structure import Scene
from app.services.dialogue_audio_service import generate_scene_dialogue_audio
from app.services.duration_orchestrator.nodes import (
    allocate_budget_node,
    final_validation_node,
)
from app.services.duration_orchestrator.state import SceneBudget
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def _scene_to_dict(scene: Scene) -> Dict[str, Any]:
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


async def generate_dialogue_with_duration_control(
    db: Session,
    *,
    story: Story,
    episode: Episode,
    script: Script,
    scenes: List[Scene],
    tts_model: str = "speech-2.6-hd",
    overwrite_beats: bool = True,
    timing_model: Optional[str] = None,
    progress_callback: Optional[callable] = None,
) -> Dict[str, Any]:
    """
    使用 Duration Orchestrator 进行时长精控对白生成。

    混合模式流程：
    1. 使用 allocate_budget_node 分配场景时长预算
    2. 对每个场景调用 generate_scene_dialogue_audio（现有流程）
    3. 使用 final_validation_node 验证总时长

    Args:
        db: 数据库会话
        story: Story 对象
        episode: Episode 对象
        script: Script 对象
        scenes: Scene 对象列表
        tts_model: TTS 模型
        overwrite_beats: 是否覆盖已有 beats
        timing_model: 时间轴计算 LLM 模型
        progress_callback: 进度回调函数

    Returns:
        包含预算分配、生成结果和验证信息的字典
    """
    total_duration_minutes = getattr(episode, "duration_minutes", None) or 3
    scenes_data = [_scene_to_dict(s) for s in scenes]

    logger.info(
        "generate_dialogue_with_duration_control: 开始时长精控",
        extra={
            "episode_id": episode.id,
            "script_id": script.id,
            "scene_count": len(scenes),
            "total_duration_minutes": total_duration_minutes,
        },
    )

    # Phase 1: 预算分配
    budget_state = {
        "episode_id": episode.id,
        "script_id": script.id,
        "total_duration_minutes": total_duration_minutes,
        "scenes_from_episode": scenes_data,
        "scene_budgets": [],
        "reasoning": [],
        "errors": [],
    }

    budget_result = allocate_budget_node(budget_state)
    scene_budgets: List[SceneBudget] = budget_result.get("scene_budgets", [])

    if not scene_budgets:
        logger.error("generate_dialogue_with_duration_control: 预算分配失败")
        return {
            "success": False,
            "error": "budget_allocation_failed",
            "reasoning": budget_result.get("reasoning", []),
        }

    # 创建场景编号到预算的映射
    budget_map = {b.scene_number: b for b in scene_budgets}

    if progress_callback:
        progress_callback(f"预算分配完成，开始生成 {len(scenes)} 个场景")

    # Phase 2: 使用现有流程生成每个场景的对白音轨
    generation_results = []
    total_actual_duration = 0.0

    for idx, scene in enumerate(scenes, start=1):
        scene_number = getattr(scene, "scene_number", idx)
        budget = budget_map.get(scene_number)

        # 使用预算分配的目标时长，否则回退到场景估算或均分
        target_duration = None
        if budget:
            target_duration = budget.target_duration_seconds
        elif not target_duration:
            target_duration = getattr(scene, "estimated_duration_seconds", None)
        if not target_duration:
            target_duration = (total_duration_minutes * 60) // len(scenes)

        if progress_callback:
            progress_callback(
                f"生成场景 {scene_number}/{len(scenes)} " f"(目标 {target_duration}s)"
            )

        logger.info(
            "generate_dialogue_with_duration_control: 生成场景 %d",
            scene_number,
            extra={
                "scene_number": scene_number,
                "target_duration_seconds": target_duration,
            },
        )

        try:
            # 调用现有的对白音轨生成
            await generate_scene_dialogue_audio(
                db,
                story=story,
                episode=episode,
                script=script,
                scene=scene,
                tts_model=tts_model,
                overwrite_beats=overwrite_beats,
                timing_model=timing_model,
                target_duration_seconds=target_duration,
            )

            # 获取实际生成的时长（从 scene 的 beats 中计算）
            actual_duration = _get_scene_actual_duration(db, scene)
            total_actual_duration += actual_duration

            # 更新预算中的实际时长
            if budget:
                budget.actual_duration_seconds = actual_duration

            generation_results.append(
                {
                    "scene_number": scene_number,
                    "target_duration": target_duration,
                    "actual_duration": actual_duration,
                    "success": True,
                }
            )

        except Exception as exc:
            logger.exception(
                "generate_dialogue_with_duration_control: 场景 %d 生成失败",
                scene_number,
            )
            generation_results.append(
                {
                    "scene_number": scene_number,
                    "target_duration": target_duration,
                    "error": str(exc),
                    "success": False,
                }
            )

    # Phase 3: 最终验证
    validation_state = {
        "episode_id": episode.id,
        "total_duration_minutes": total_duration_minutes,
        "statistics": {
            "total_actual_duration_seconds": total_actual_duration,
        },
        "reasoning": budget_result.get("reasoning", []),
        "errors": [],
    }

    validation_result = final_validation_node(validation_state)
    final_validation = validation_result.get("final_validation_result", {})
    success = final_validation.get("passed", False)

    # 统计失败的场景
    failed_scenes = [r for r in generation_results if not r.get("success")]
    if failed_scenes:
        success = False

    logger.info(
        "generate_dialogue_with_duration_control: 完成",
        extra={
            "episode_id": episode.id,
            "success": success,
            "total_actual_duration": total_actual_duration,
            "total_target_duration": total_duration_minutes * 60,
            "duration_ratio": final_validation.get("duration_ratio", 0),
            "failed_scene_count": len(failed_scenes),
        },
    )

    return {
        "success": success,
        "episode_id": episode.id,
        "script_id": script.id,
        # 预算信息
        "scene_budgets": [b.to_dict() for b in scene_budgets],
        # 生成结果
        "generation_results": generation_results,
        # 统计信息
        "statistics": {
            "total_target_duration_seconds": total_duration_minutes * 60,
            "total_actual_duration_seconds": total_actual_duration,
            "duration_ratio": final_validation.get("duration_ratio", 0),
            "scene_count": len(scenes),
            "successful_count": len(scenes) - len(failed_scenes),
            "failed_count": len(failed_scenes),
        },
        # 验证结果
        "final_validation": final_validation,
        # 推理日志
        "reasoning": validation_result.get("reasoning", []),
        "errors": validation_result.get("errors", []),
    }


def _get_scene_actual_duration(db: Session, scene: Scene) -> float:
    """从 SceneBeat 记录中计算场景实际时长。"""
    from app.models.story_structure import SceneBeat

    beats = (
        db.query(SceneBeat)
        .filter(SceneBeat.scene_id == scene.id)
        .filter(SceneBeat.is_deleted == False)  # noqa: E712
        .all()
    )

    total_duration = 0.0
    for beat in beats:
        if beat.duration_seconds:
            total_duration += float(beat.duration_seconds)

    return total_duration
