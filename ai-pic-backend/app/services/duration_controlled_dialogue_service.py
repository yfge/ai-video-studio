"""
时长精控对白生成服务

混合模式：使用 Duration Orchestrator 进行预算分配和验证，
使用模块化 scene audio generator 进行实际 TTS 生成。
"""

import logging
import time
from typing import Any, Callable, Dict, List, Optional

from app.models.script import Episode, Script, Story
from app.models.story_structure import Scene
from app.services.duration_controlled_scene_runner import (
    generate_scene_audio_with_budgets,
)
from app.services.duration_orchestrator.nodes import (
    allocate_budget_node,
    final_validation_node,
)
from app.services.duration_orchestrator.state import SceneBudget
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# 日志前缀，便于日志过滤
LOG_PREFIX = "DurationControl"


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
    progress_callback: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    """使用 Duration Orchestrator 进行时长精控对白生成。"""
    start_time = time.time()
    total_duration_minutes = getattr(episode, "duration_minutes", None) or 3
    scenes_data = [_scene_to_dict(s) for s in scenes]

    logger.info(
        f"{LOG_PREFIX}: 开始时长精控流程",
        extra={
            "phase": "start",
            "episode_id": episode.id,
            "script_id": script.id,
            "story_id": story.id,
            "scene_count": len(scenes),
            "total_duration_minutes": total_duration_minutes,
            "tts_model": tts_model,
        },
    )

    # ========== Phase 1: 预算分配 ==========
    phase1_start = time.time()
    if progress_callback:
        progress_callback("Phase 1/3: 分配场景时长预算...")

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
    phase1_duration = time.time() - phase1_start

    if not scene_budgets:
        logger.error(
            f"{LOG_PREFIX}: 预算分配失败",
            extra={
                "phase": "budget_allocation",
                "episode_id": episode.id,
                "duration_ms": int(phase1_duration * 1000),
            },
        )
        return {
            "success": False,
            "error": "budget_allocation_failed",
            "reasoning": budget_result.get("reasoning", []),
            "timing": {"phase1_budget_ms": int(phase1_duration * 1000)},
        }

    # 记录预算分配结果
    budget_summary = [
        {"scene": b.scene_number, "target_s": b.target_duration_seconds}
        for b in scene_budgets
    ]
    logger.info(
        f"{LOG_PREFIX}: 预算分配完成",
        extra={
            "phase": "budget_allocation",
            "episode_id": episode.id,
            "scene_count": len(scene_budgets),
            "budgets": budget_summary,
            "duration_ms": int(phase1_duration * 1000),
        },
    )

    # ========== Phase 2: 逐场景生成 ==========
    phase2 = await generate_scene_audio_with_budgets(
        db,
        story=story,
        episode=episode,
        script=script,
        scenes=scenes,
        scene_budgets=scene_budgets,
        total_duration_minutes=total_duration_minutes,
        tts_model=tts_model,
        overwrite_beats=overwrite_beats,
        timing_model=timing_model,
        progress_callback=progress_callback,
        logger=logger,
        log_prefix=LOG_PREFIX,
    )
    generation_results = phase2["generation_results"]
    total_actual_duration = phase2["total_actual_duration"]
    scene_timings = phase2["scene_timings"]
    phase2_duration = phase2["phase_duration"]

    # ========== Phase 3: 最终验证 ==========
    phase3_start = time.time()
    if progress_callback:
        progress_callback("Phase 3/3: 验证总时长...")

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
    phase3_duration = time.time() - phase3_start

    # 统计失败的场景
    failed_scenes = [r for r in generation_results if not r.get("success")]
    if failed_scenes:
        success = False

    total_time = time.time() - start_time
    duration_ratio = final_validation.get("duration_ratio", 0)

    # 最终日志
    logger.info(
        f"{LOG_PREFIX}: 流程完成",
        extra={
            "phase": "complete",
            "episode_id": episode.id,
            "success": success,
            "total_target_duration": total_duration_minutes * 60,
            "total_actual_duration": round(total_actual_duration, 2),
            "duration_ratio": round(duration_ratio, 4),
            "validation_passed": final_validation.get("passed", False),
            "scene_count": len(scenes),
            "failed_count": len(failed_scenes),
            "timing": {
                "total_ms": int(total_time * 1000),
                "phase1_budget_ms": int(phase1_duration * 1000),
                "phase2_generation_ms": int(phase2_duration * 1000),
                "phase3_validation_ms": int(phase3_duration * 1000),
                "avg_scene_ms": (
                    int(sum(scene_timings) / len(scene_timings)) if scene_timings else 0
                ),
            },
        },
    )

    if progress_callback:
        status = "通过" if success else "未通过"
        progress_callback(
            f"完成: {status} (时长比 {duration_ratio:.1%}, " f"耗时 {total_time:.1f}s)"
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
            "total_actual_duration_seconds": round(total_actual_duration, 2),
            "duration_ratio": round(duration_ratio, 4),
            "scene_count": len(scenes),
            "successful_count": len(scenes) - len(failed_scenes),
            "failed_count": len(failed_scenes),
        },
        # 验证结果
        "final_validation": final_validation,
        # 时序信息
        "timing": {
            "total_ms": int(total_time * 1000),
            "phase1_budget_ms": int(phase1_duration * 1000),
            "phase2_generation_ms": int(phase2_duration * 1000),
            "phase3_validation_ms": int(phase3_duration * 1000),
        },
        # 推理日志
        "reasoning": validation_result.get("reasoning", []),
        "errors": validation_result.get("errors", []),
    }
