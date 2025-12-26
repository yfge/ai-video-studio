"""
时长精控对白生成服务

混合模式：使用 Duration Orchestrator 进行预算分配和验证，
使用现有 dialogue_audio_service 进行实际 TTS 生成。
"""

import logging
import time
from typing import Any, Callable, Dict, List, Optional

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

    # 创建场景编号到预算的映射
    budget_map = {b.scene_number: b for b in scene_budgets}

    if progress_callback:
        progress_callback(f"Phase 2/3: 生成 {len(scenes)} 个场景对白音轨...")

    # ========== Phase 2: 逐场景生成 ==========
    phase2_start = time.time()
    generation_results = []
    total_actual_duration = 0.0
    scene_timings = []

    for idx, scene in enumerate(scenes, start=1):
        scene_start = time.time()
        scene_number = getattr(scene, "scene_number", idx)
        budget = budget_map.get(scene_number)

        # 使用预算分配的目标时长，否则回退到场景估算或均分
        target_duration = None
        if budget:
            target_duration = budget.target_duration_seconds
        if not target_duration:
            target_duration = getattr(scene, "estimated_duration_seconds", None)
        if not target_duration:
            target_duration = (total_duration_minutes * 60) // len(scenes)

        if progress_callback:
            progress_callback(
                f"场景 {idx}/{len(scenes)}: 生成中 (目标 {target_duration:.0f}s)"
            )

        logger.info(
            f"{LOG_PREFIX}: 开始生成场景 {scene_number}",
            extra={
                "phase": "scene_generation",
                "episode_id": episode.id,
                "scene_number": scene_number,
                "scene_index": idx,
                "scene_total": len(scenes),
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
            scene_duration_ms = int((time.time() - scene_start) * 1000)

            # 计算偏差
            deviation = actual_duration - target_duration
            deviation_pct = (
                (deviation / target_duration * 100) if target_duration else 0
            )

            # 更新预算中的实际时长
            if budget:
                budget.actual_duration_seconds = actual_duration

            generation_results.append(
                {
                    "scene_number": scene_number,
                    "target_duration": target_duration,
                    "actual_duration": actual_duration,
                    "deviation_seconds": round(deviation, 2),
                    "deviation_percent": round(deviation_pct, 1),
                    "success": True,
                    "generation_ms": scene_duration_ms,
                }
            )

            scene_timings.append(scene_duration_ms)

            logger.info(
                f"{LOG_PREFIX}: 场景 {scene_number} 生成完成",
                extra={
                    "phase": "scene_generation",
                    "episode_id": episode.id,
                    "scene_number": scene_number,
                    "target_duration": target_duration,
                    "actual_duration": actual_duration,
                    "deviation_seconds": round(deviation, 2),
                    "deviation_percent": round(deviation_pct, 1),
                    "generation_ms": scene_duration_ms,
                },
            )

            if progress_callback:
                progress_callback(
                    f"场景 {idx}/{len(scenes)}: 完成 "
                    f"({actual_duration:.1f}s, 偏差 {deviation_pct:+.0f}%)"
                )

        except Exception as exc:
            scene_duration_ms = int((time.time() - scene_start) * 1000)
            logger.exception(
                f"{LOG_PREFIX}: 场景 {scene_number} 生成失败",
                extra={
                    "phase": "scene_generation",
                    "episode_id": episode.id,
                    "scene_number": scene_number,
                    "error": str(exc),
                    "generation_ms": scene_duration_ms,
                },
            )
            generation_results.append(
                {
                    "scene_number": scene_number,
                    "target_duration": target_duration,
                    "error": str(exc),
                    "success": False,
                    "generation_ms": scene_duration_ms,
                }
            )

            if progress_callback:
                progress_callback(f"场景 {idx}/{len(scenes)}: 失败 - {str(exc)[:50]}")

    phase2_duration = time.time() - phase2_start

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
