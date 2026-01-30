"""
Duration Orchestrator Agent

基于 LangGraph 的端到端时长闭环验证系统。

核心流程：
1. allocate_budget: 分配场景时长预算
2. generate_dialogue: 生成符合字数约束的对白
3. tts_trial: 估算/测量实际时长
4. validate_duration: 验证时长是否达标
5. commit_scene / prepare_retry: 提交或准备重试
6. assemble_episode: 组装最终剧集
7. final_validation: 验证总时长 ±10%
"""

import logging
from typing import Any, Callable, Dict, List, Optional

from app.core.logging import get_logger

from app.services.duration_orchestrator.nodes import (
    allocate_budget_node,
    assemble_episode_node,
    commit_scene_node,
    final_validation_node,
    generate_dialogue_node,
    prepare_retry_node,
    should_commit_or_retry,
    should_continue_or_assemble,
    should_proceed_to_generation,
    should_proceed_to_tts,
    tts_trial_node,
    validate_duration_node,
)

try:
    from langgraph.graph import END, StateGraph

    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False

logger = get_logger()

# Progress callback type
ProgressCallback = Callable[[str, Dict[str, Any]], None]


class DurationOrchestratorAgent:
    """
    Duration Orchestrator Agent - 端到端时长闭环验证。

    通过场景级闭环验证确保剧集时长符合目标：
    - 每个场景生成后立即验证时长
    - 不达标则重新生成（最多3次）
    - 达标后锁定并调整后续场景预算
    """

    def __init__(
        self,
        script_agent=None,
        tts_service=None,
        use_actual_tts: bool = False,
        progress_callback: Optional[ProgressCallback] = None,
    ):
        """
        初始化 Duration Orchestrator。

        Args:
            script_agent: ScriptLangGraphAgent 实例，用于生成对白
            tts_service: TTS 服务实例，用于实际时长测量
            use_actual_tts: 是否使用实际 TTS（False 则使用字数估算）
            progress_callback: 可选的进度回调函数，签名为 (event: str, data: dict) -> None
        """
        self.script_agent = script_agent
        self.tts_service = tts_service
        self.use_actual_tts = use_actual_tts
        self.progress_callback = progress_callback
        self.logger = logger

    def _emit_progress(self, event: str, data: Dict[str, Any]) -> None:
        """Emit a progress event if callback is configured."""
        if self.progress_callback:
            try:
                self.progress_callback(event, data)
            except Exception as exc:
                self.logger.warning(
                    "Progress callback failed",
                    extra={"event": event, "error": str(exc)},
                )
        # Also log the event for audit trail
        self.logger.info(
            f"duration_orchestrator_progress: {event}",
            extra={"event": event, **data},
        )

    def _build_graph(self) -> "StateGraph":
        """
        构建 LangGraph StateGraph。

        节点流程:
            allocate_budget
                ↓
            generate_dialogue ←─────────────┐
                ↓                           │
            tts_trial                       │
                ↓                           │
            validate_duration               │
                ↓                           │
            ┌───┴───┐                       │
            │       │                       │
        commit   prepare_retry ─────────────┘
            │
            ↓
        ┌───┴───┐
        │       │
        continue assemble_episode
        (loop)    ↓
             final_validation
                  ↓
                 END
        """
        graph = StateGraph(dict)

        # 添加所有节点
        graph.add_node("allocate_budget", allocate_budget_node)
        graph.add_node("generate_dialogue", generate_dialogue_node)
        graph.add_node("tts_trial", tts_trial_node)
        graph.add_node("validate_duration", validate_duration_node)
        graph.add_node("commit_scene", commit_scene_node)
        graph.add_node("prepare_retry", prepare_retry_node)
        graph.add_node("assemble_episode", assemble_episode_node)
        graph.add_node("final_validation", final_validation_node)

        # 设置入口点
        graph.set_entry_point("allocate_budget")

        # allocate_budget → generate_dialogue 或 assemble_episode (空场景跳过)
        graph.add_conditional_edges(
            "allocate_budget",
            should_proceed_to_generation,
            {
                "generate": "generate_dialogue",
                "assemble": "assemble_episode",
                "failed": END,
            },
        )

        # generate_dialogue → tts_trial 或 retry
        graph.add_conditional_edges(
            "generate_dialogue",
            should_proceed_to_tts,
            {
                "tts": "tts_trial",
                "retry": "generate_dialogue",
                "failed": END,
            },
        )

        # tts_trial → validate_duration
        graph.add_edge("tts_trial", "validate_duration")

        # validate_duration → commit_scene 或 prepare_retry
        graph.add_conditional_edges(
            "validate_duration",
            should_commit_or_retry,
            {
                "commit": "commit_scene",
                "retry": "prepare_retry",
                "next": "commit_scene",
            },
        )

        # prepare_retry → generate_dialogue (重新生成)
        graph.add_edge("prepare_retry", "generate_dialogue")

        # commit_scene → continue (下一个场景) 或 assemble_episode (完成)
        graph.add_conditional_edges(
            "commit_scene",
            should_continue_or_assemble,
            {
                "continue": "generate_dialogue",
                "assemble": "assemble_episode",
            },
        )

        # assemble_episode → final_validation
        graph.add_edge("assemble_episode", "final_validation")

        # final_validation → END
        graph.add_edge("final_validation", END)

        return graph

    async def orchestrate(
        self,
        *,
        episode_id: int,
        script_id: int,
        story_id: int,
        total_duration_minutes: int,
        scenes: List[Dict[str, Any]],
        episode: Dict[str, Any],
        story: Dict[str, Any],
        generation_config: Optional[Dict[str, Any]] = None,
        voice_config: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> Dict[str, Any]:
        """
        执行端到端时长闭环验证。

        Args:
            episode_id: 剧集 ID
            script_id: 剧本 ID
            story_id: 故事 ID
            total_duration_minutes: 目标总时长（分钟）
            scenes: 场景列表（来自 Episode Agent）
            episode: Episode 数据
            story: Story 数据
            generation_config: 对白生成配置
            voice_config: TTS 语音配置
            progress_callback: 可选的进度回调函数（覆盖实例级回调）

        Returns:
            包含所有场景对白、时长信息和推理日志的结果字典
        """
        # Use method-level callback if provided, otherwise fall back to instance
        callback = progress_callback or self.progress_callback
        if callback and callback != self.progress_callback:
            self.progress_callback = callback

        if not LANGGRAPH_AVAILABLE:
            self.logger.error("LangGraph not available")
            return {
                "success": False,
                "error": "langgraph_not_available",
            }

        # 构建初始状态
        initial_state = {
            # 基础信息
            "episode_id": episode_id,
            "script_id": script_id,
            "story_id": story_id,
            "total_duration_minutes": total_duration_minutes,
            "scenes_from_episode": scenes,
            # 上下文数据
            "episode": episode,
            "story": story,
            "generation_config": generation_config or {},
            "voice_config": voice_config or {},
            # 服务实例
            "script_agent": self.script_agent,
            "tts_service": self.tts_service,
            "use_actual_tts": self.use_actual_tts,
            # 状态追踪
            "scene_budgets": [],
            "current_scene_index": 0,
            "generated_dialogues": {},
            "committed_scenes": {},
            "phase": "allocating",
            "reasoning": [],
            "errors": [],
        }

        self.logger.info(
            "DurationOrchestratorAgent: 开始编排",
            extra={
                "episode_id": episode_id,
                "total_duration_minutes": total_duration_minutes,
                "scene_count": len(scenes),
                "use_actual_tts": self.use_actual_tts,
            },
        )

        # Emit orchestration_started event
        self._emit_progress("orchestration_started", {
            "episode_id": episode_id,
            "script_id": script_id,
            "total_duration_minutes": total_duration_minutes,
            "scene_count": len(scenes),
        })

        # 构建并执行图
        graph = self._build_graph()
        app = graph.compile()

        try:
            result = await app.ainvoke(initial_state)
        except Exception as exc:
            self.logger.exception("DurationOrchestratorAgent: 执行失败")
            return {
                "success": False,
                "error": str(exc),
                "reasoning": initial_state.get("reasoning", []),
            }

        # 提取结果
        scene_budgets = result.get("scene_budgets", [])
        committed_scenes = result.get("committed_scenes", {})
        errors = result.get("errors", [])

        # 从 assemble_episode 和 final_validation 节点获取结果
        assembled_episode = result.get("assembled_episode", {})
        final_validation = result.get("final_validation_result", {})
        statistics = result.get("statistics", {})

        # 如果没有统计信息（可能图未完整执行），手动计算
        if not statistics:
            total_actual_duration = sum(
                b.actual_duration_seconds or 0 for b in scene_budgets
            )
            total_target_duration = total_duration_minutes * 60
            duration_ratio = (
                total_actual_duration / total_target_duration
                if total_target_duration > 0
                else 0
            )
            total_retries = sum(b.attempt_count for b in scene_budgets)
            avg_retries = total_retries / len(scene_budgets) if scene_budgets else 0

            statistics = {
                "total_target_duration_seconds": total_target_duration,
                "total_actual_duration_seconds": total_actual_duration,
                "duration_ratio": round(duration_ratio, 4),
                "scene_count": len(scene_budgets),
                "total_retries": total_retries,
                "avg_retries_per_scene": round(avg_retries, 2),
            }

        # 确定最终成功状态（基于 final_validation 结果）
        success = result.get("success", len(errors) == 0)
        if final_validation:
            success = final_validation.get("passed", success) and len(errors) == 0

        self.logger.info(
            "DurationOrchestratorAgent: 编排完成",
            extra={
                "episode_id": episode_id,
                "scene_count": statistics.get("scene_count", len(scene_budgets)),
                "total_actual_duration": statistics.get(
                    "total_actual_duration_seconds", 0
                ),
                "total_target_duration": statistics.get(
                    "total_target_duration_seconds", 0
                ),
                "duration_ratio": statistics.get("duration_ratio", 0),
                "total_retries": statistics.get("total_retries", 0),
                "avg_retries": statistics.get("avg_retries_per_scene", 0),
                "error_count": len(errors),
                "final_validation_passed": final_validation.get("passed"),
            },
        )

        # Emit orchestration_completed event
        self._emit_progress("orchestration_completed", {
            "episode_id": episode_id,
            "success": success,
            "scene_count": statistics.get("scene_count", len(scene_budgets)),
            "total_actual_duration_seconds": statistics.get(
                "total_actual_duration_seconds", 0
            ),
            "total_target_duration_seconds": statistics.get(
                "total_target_duration_seconds", 0
            ),
            "duration_ratio": statistics.get("duration_ratio", 0),
            "total_retries": statistics.get("total_retries", 0),
            "error_count": len(errors),
        })

        return {
            "success": success,
            "episode_id": episode_id,
            "script_id": script_id,
            # 场景结果
            "scene_budgets": [b.to_dict() for b in scene_budgets],
            "committed_scenes": committed_scenes,
            "generated_dialogues": result.get("generated_dialogues", {}),
            # 组装结果
            "assembled_episode": assembled_episode,
            # 最终验证结果
            "final_validation": final_validation,
            # 统计信息
            "statistics": statistics,
            # 日志
            "reasoning": result.get("reasoning", []),
            "errors": errors,
        }


async def orchestrate_episode_duration(
    *,
    episode_id: int,
    script_id: int,
    story_id: int,
    total_duration_minutes: int,
    scenes: List[Dict[str, Any]],
    episode: Dict[str, Any],
    story: Dict[str, Any],
    script_agent=None,
    tts_service=None,
    use_actual_tts: bool = False,
    generation_config: Optional[Dict[str, Any]] = None,
    voice_config: Optional[Dict[str, Any]] = None,
    progress_callback: Optional[ProgressCallback] = None,
) -> Dict[str, Any]:
    """
    便捷函数：执行剧集时长编排。

    这是 DurationOrchestratorAgent.orchestrate() 的简化封装。

    Args:
        episode_id: 剧集 ID
        script_id: 剧本 ID
        story_id: 故事 ID
        total_duration_minutes: 目标总时长（分钟）
        scenes: 场景列表（来自 Episode Agent）
        episode: Episode 数据
        story: Story 数据
        script_agent: ScriptLangGraphAgent 实例
        tts_service: TTS 服务实例
        use_actual_tts: 是否使用实际 TTS
        generation_config: 对白生成配置
        voice_config: TTS 语音配置
        progress_callback: 进度回调函数 (event: str, data: dict) -> None

    Returns:
        包含所有场景对白、时长信息和推理日志的结果字典
    """
    agent = DurationOrchestratorAgent(
        script_agent=script_agent,
        tts_service=tts_service,
        use_actual_tts=use_actual_tts,
        progress_callback=progress_callback,
    )

    return await agent.orchestrate(
        episode_id=episode_id,
        script_id=script_id,
        story_id=story_id,
        total_duration_minutes=total_duration_minutes,
        scenes=scenes,
        episode=episode,
        story=story,
        generation_config=generation_config,
        voice_config=voice_config,
    )
