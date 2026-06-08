"""
ReactAgentBase-based Timeline Agent for intelligent gap calculation.

Replaces the LangGraph implementation with the universal agent framework,
providing standardized error handling, repair strategies, and monitoring.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from app.core.logging import get_logger
from app.services.agent_core import (
    AgentError,
    AgentErrorType,
    AgentState,
    FailureMode,
    FailurePatternMatcher,
    ReactAgentBase,
    RepairMonitor,
    RepairStrategy,
)
from app.utils.json_utils import extract_json_block

from .constants import (
    MAX_AVG_GAP_MS,
    MAX_GAP_MS,
    MAX_REPAIR_ATTEMPTS,
    MIN_AVG_GAP_MS,
    MIN_GAP_MS,
    TIMELINE_REPAIR_PROMPT,
    TIMELINE_SYSTEM_PROMPT,
)
from .schemas import TIMING_OUTPUT_SCHEMA, TimingDecision, TimingPlan
from .utils import (
    build_dialogue_contexts,
    build_scene_context,
    calculate_fallback_timing,
    calculate_rhythm_score,
    format_dialogue_for_prompt,
)

if TYPE_CHECKING:
    from app.services.ai_service import AIService

logger = get_logger()


class TimelineReactAgent(ReactAgentBase[TimingPlan]):
    """ReactAgentBase-based Timeline Agent.

    Computes intelligent timing gaps for dialogue sequences using LLM
    with standardized error handling and repair strategies.
    """

    def __init__(
        self,
        service: "AIService",
        repair_monitor: Optional[RepairMonitor] = None,
    ) -> None:
        """Initialize with AI service reference.

        Args:
            service: AI service for LLM calls
            repair_monitor: Optional monitor for tracking repair success
        """
        super().__init__(
            max_attempts=MAX_REPAIR_ATTEMPTS + 1,
            repair_strategies={
                AgentErrorType.SYNTAX: RepairStrategy.REFINE,
                AgentErrorType.VALIDATION: RepairStrategy.REFINE,
                AgentErrorType.BUDGET: RepairStrategy.SIMPLIFY,
                AgentErrorType.NETWORK: RepairStrategy.RETRY,
            },
        )
        self.service = service
        self.repair_monitor = repair_monitor or RepairMonitor()
        self._pattern_matcher = FailurePatternMatcher()

        # LLM parameters (set per-call)
        self._model: Optional[str] = None
        self._prefer_provider: Optional[str] = None
        self._temperature: float = 0.4

    async def compute_timing(
        self,
        *,
        dialogues: List[Dict[str, Any]],
        stage_directions: List[Dict[str, Any]],
        scene_context: Dict[str, Any],
        model: Optional[str] = None,
        prefer_provider: Optional[str] = None,
        temperature: float = 0.4,
        target_duration_seconds: Optional[int] = None,
    ) -> Optional[TimingPlan]:
        """Main entry point for computing intelligent timing.

        Args:
            dialogues: List of dialogue segments
            stage_directions: List of stage directions
            scene_context: Scene context information
            model: Optional model override
            prefer_provider: Optional provider preference
            temperature: LLM temperature
            target_duration_seconds: Optional target scene duration

        Returns:
            TimingPlan or None if unavailable
        """
        if not self.service.ai_manager:
            logger.warning("AI manager not available, using fallback")
            return self._compute_fallback(dialogues, scene_context)

        # Store LLM params
        self._model = model
        self._prefer_provider = prefer_provider
        self._temperature = temperature

        # Build input data
        input_data = {
            "dialogues": dialogues,
            "stage_directions": stage_directions,
            "scene_context_raw": scene_context,
            "target_duration_seconds": target_duration_seconds,
        }

        # Run agent
        start_time = time.time()
        result = await self.run(input_data)
        duration_ms = (time.time() - start_time) * 1000

        if result.success and result.data:
            return result.data

        # Record failure and use fallback
        if result.errors:
            error = result.errors[0]
            self.repair_monitor.record(
                failure_mode=self._classify_failure_mode(error),
                strategy="fallback",
                success=False,
                duration_ms=duration_ms,
                error_before=error.message,
            )

        return self._compute_fallback(dialogues, scene_context)

    async def _generate(
        self,
        input_data: Dict[str, Any],
        state: AgentState,
    ) -> Any:
        """Generate timing decisions via LLM.

        Args:
            input_data: Input containing dialogues and scene context
            state: Current agent state

        Returns:
            Raw LLM output string
        """
        # Prepare context
        dialogues = input_data.get("dialogues", [])
        scene_ctx_raw = input_data.get("scene_context_raw", {})
        target_duration = input_data.get("target_duration_seconds")

        dialogue_contexts = build_dialogue_contexts(dialogues)
        scene_context = build_scene_context(
            scene_id=scene_ctx_raw.get("scene_id", 0),
            scene_number=scene_ctx_raw.get("scene_number", 1),
            dialogues=dialogues,
            conflict_notes=scene_ctx_raw.get("conflict_notes"),
            dramatic_question=scene_ctx_raw.get("dramatic_question"),
            slug_line=scene_ctx_raw.get("slug_line"),
            location=scene_ctx_raw.get("location"),
            time_of_day=scene_ctx_raw.get("time_of_day"),
            summary=scene_ctx_raw.get("summary"),
            primary_characters=scene_ctx_raw.get("primary_characters"),
        )

        # Store for validation
        state.context["dialogue_contexts"] = [c.model_dump() for c in dialogue_contexts]
        state.context["scene_context"] = scene_context.model_dump()

        # Build prompt
        prompt = self._build_reasoning_prompt(
            scene_context.model_dump(),
            [c.model_dump() for c in dialogue_contexts],
            target_duration,
        )

        # Check for repair feedback
        if "_error_feedback" in input_data:
            prompt = self._build_repair_prompt(input_data, state)

        # Call LLM
        resp = await self.service.ai_manager.generate_text(
            prompt=prompt,
            temperature=self._temperature,
            model=self._model,
            prefer_provider=self._prefer_provider,
            json_schema={
                "name": "timeline_timing",
                "schema": TIMING_OUTPUT_SCHEMA,
            },
            system_prompt=TIMELINE_SYSTEM_PROMPT,
        )

        state.context["provider_used"] = resp.provider
        state.context["model_used"] = resp.model

        return resp.data if isinstance(resp.data, str) else str(resp.data or "")

    def _parse_result(self, raw_result: Any) -> Optional[TimingPlan]:
        """Parse LLM output into TimingPlan.

        Args:
            raw_result: Raw LLM output

        Returns:
            TimingPlan or None if parsing fails
        """
        if not raw_result:
            return None

        parsed = extract_json_block(raw_result)
        if not parsed:
            return None

        # Build decisions from parsed output
        decisions = []
        for rd in parsed.get("timing_decisions", []):
            decisions.append(
                TimingDecision(
                    segment_index=rd.get("segment_index", 0),
                    gap_type=rd.get("gap_type", "post_dialogue"),
                    base_duration_ms=300,
                    adjusted_duration_ms=rd.get("duration_ms", 300),
                    reasoning=rd.get("reasoning", ""),
                )
            )

        if not decisions:
            return None

        total_gap = sum(d.adjusted_duration_ms for d in decisions)
        avg_gap = total_gap / len(decisions) if decisions else 0
        rhythm_score = calculate_rhythm_score(decisions)

        return TimingPlan(
            scene_id=0,  # Will be set from context
            decisions=decisions,
            total_gap_ms=total_gap,
            avg_gap_ms=avg_gap,
            rhythm_score=rhythm_score,
            reasoning_summary=parsed.get("overall_rhythm_note", ""),
        )

    def _validate(
        self,
        result: TimingPlan,
        state: AgentState,
    ) -> List[AgentError]:
        """Validate timing plan against constraints.

        Args:
            result: Parsed TimingPlan
            state: Current agent state

        Returns:
            List of validation errors
        """
        errors = []
        decisions = result.decisions

        # Validate individual gaps
        for d in decisions:
            dur = d.adjusted_duration_ms
            idx = d.segment_index
            if dur < MIN_GAP_MS:
                errors.append(
                    AgentError(
                        error_type=AgentErrorType.VALIDATION,
                        message=f"gap_{idx}_too_short: {dur}ms < {MIN_GAP_MS}ms",
                        details={"segment_index": idx, "duration": dur},
                        recoverable=True,
                    )
                )
            if dur > MAX_GAP_MS:
                errors.append(
                    AgentError(
                        error_type=AgentErrorType.VALIDATION,
                        message=f"gap_{idx}_too_long: {dur}ms > {MAX_GAP_MS}ms",
                        details={"segment_index": idx, "duration": dur},
                        recoverable=True,
                    )
                )

        # Validate average gap
        avg_gap = result.avg_gap_ms
        if avg_gap < MIN_AVG_GAP_MS:
            errors.append(
                AgentError(
                    error_type=AgentErrorType.VALIDATION,
                    message=f"avg_gap_too_short: {avg_gap:.0f}ms",
                    recoverable=True,
                )
            )
        if avg_gap > MAX_AVG_GAP_MS:
            errors.append(
                AgentError(
                    error_type=AgentErrorType.VALIDATION,
                    message=f"avg_gap_too_long: {avg_gap:.0f}ms",
                    recoverable=True,
                )
            )

        # Check rhythm monotony
        if len(decisions) > 3:
            durations = [d.adjusted_duration_ms for d in decisions]
            if len(set(durations)) == 1:
                errors.append(
                    AgentError(
                        error_type=AgentErrorType.VALIDATION,
                        message="rhythm_too_monotonous",
                        recoverable=True,
                    )
                )

        # Duration validation against target
        target_duration = state.context.get("target_duration_seconds")
        if target_duration:
            self._validate_duration(result, state, errors, target_duration)

        return errors

    def _validate_duration(
        self,
        result: TimingPlan,
        state: AgentState,
        errors: List[AgentError],
        target_duration_seconds: int,
    ) -> None:
        """Validate timing against target duration."""
        total_gap_ms = result.total_gap_ms
        dialogue_contexts = state.context.get("dialogue_contexts", [])

        has_actual_durations = any(
            d.get("actual_duration_ms") for d in dialogue_contexts
        )
        dialogue_duration_ms = sum(
            (d.get("actual_duration_ms") or d.get("estimated_duration_ms") or 0)
            for d in dialogue_contexts
        )

        computed_total_ms = dialogue_duration_ms + total_gap_ms
        target_ms = target_duration_seconds * 1000
        duration_ratio = computed_total_ms / target_ms if target_ms > 0 else 0

        logger.info(
            "Timeline Agent duration validation",
            extra={
                "target_duration_seconds": target_duration_seconds,
                "dialogue_duration_ms": dialogue_duration_ms,
                "total_gap_ms": total_gap_ms,
                "computed_total_ms": computed_total_ms,
                "duration_ratio": round(duration_ratio, 2),
            },
        )

        # Tolerance based on duration source
        tolerance_high = 1.2 if has_actual_durations else 1.4

        if duration_ratio > tolerance_high:
            errors.append(
                AgentError(
                    error_type=AgentErrorType.VALIDATION,
                    message=(
                        f"duration_too_long: {computed_total_ms}ms vs target "
                        f"{target_ms}ms ({duration_ratio:.0%})"
                    ),
                    recoverable=True,
                )
            )

    def _refine_input(
        self,
        input_data: Dict[str, Any],
        error: AgentError,
        state: AgentState,
    ) -> Dict[str, Any]:
        """Refine input with error feedback for repair.

        Args:
            input_data: Current input data
            error: The error that triggered repair
            state: Current agent state

        Returns:
            Modified input data with error feedback
        """
        refined = dict(input_data)
        refined["_error_feedback"] = error.message
        refined["_error_type"] = error.error_type.value
        refined["_validation_errors"] = [e.message for e in state.errors]
        refined["_proposed_plan"] = (
            state.intermediate_results[-1] if state.intermediate_results else None
        )
        return refined

    def _build_reasoning_prompt(
        self,
        scene_context: Dict[str, Any],
        dialogue_contexts: List[Dict[str, Any]],
        target_duration_seconds: Optional[int] = None,
    ) -> str:
        """Build the reasoning prompt for LLM."""
        from .schemas import DialogueContext

        contexts = [DialogueContext.model_validate(d) for d in dialogue_contexts]
        formatted = format_dialogue_for_prompt(contexts)

        # Calculate total dialogue duration
        total_dialogue_ms = sum(
            (c.actual_duration_ms or c.estimated_duration_ms or 0) for c in contexts
        )
        has_actual_durations = any(c.actual_duration_ms for c in contexts)

        # Build scene description
        slug_line = scene_context.get("slug_line") or ""
        location = scene_context.get("location") or "未知"
        time_of_day = scene_context.get("time_of_day") or "未知"
        summary = scene_context.get("summary") or ""

        scene_description = (
            f"- 场景: {slug_line}"
            if slug_line
            else f"- 地点: {location}, 时间: {time_of_day}"
        )
        summary_line = (
            f"- 场景描述: {summary[:100]}..."
            if summary and len(summary) > 100
            else (f"- 场景描述: {summary}" if summary else "")
        )

        # Build duration constraint section
        duration_constraint = ""
        if target_duration_seconds:
            target_ms = target_duration_seconds * 1000
            available_gap_ms = max(0, target_ms - total_dialogue_ms)
            avg_gap_per_dialogue = available_gap_ms // len(contexts) if contexts else 0

            duration_info = ""
            if has_actual_durations and total_dialogue_ms > 0:
                duration_info = f"""- **对白总时长**: {total_dialogue_ms}ms ({total_dialogue_ms / 1000:.1f}秒) [已由TTS生成]
- **可用于停顿的时间**: 约 {available_gap_ms}ms ({available_gap_ms / 1000:.1f}秒)
- **平均每句后停顿**: 约 {avg_gap_per_dialogue}ms"""

            duration_constraint = f"""
## 时长约束
- **目标场景时长**: {target_duration_seconds} 秒 ({target_ms} 毫秒)
{duration_info}
- 停顿时长需要合理分配，使得整体场景接近目标时长
"""

        return f"""## 场景信息
- 场景编号: {scene_context.get('scene_number', 1)}
{scene_description}
{summary_line}
- 整体情绪: {scene_context.get('mood') or '未标注'}
- 冲突程度: {scene_context.get('conflict_level', 'medium')}
- 节奏类型: {scene_context.get('pacing', 'medium')}
- 角色数量: {scene_context.get('character_count', 1)}
- 对白数量: {scene_context.get('dialogue_count', 0)}
{duration_constraint}
## 对白序列
{formatted}

## 任务
分析每句对白之后应该有多长的停顿（毫秒），考虑：
1. 情绪过渡（愤怒→平静需要更长停顿让观众消化）
2. 戏剧张力（高冲突场景需要更短停顿保持紧张感）
3. 语义完整性（句号后比逗号停顿更长）
4. 角色切换（不同角色之间需要呼吸空间）
5. 场景氛围（夜晚场景可能需要更长的呼吸空间）

输出 JSON 格式的 timing_decisions。"""

    def _build_repair_prompt(
        self,
        input_data: Dict[str, Any],
        state: AgentState,
    ) -> str:
        """Build repair prompt with error feedback."""
        errors = input_data.get("_validation_errors", [])
        plan = input_data.get("_proposed_plan")

        return TIMELINE_REPAIR_PROMPT.format(
            min_gap_ms=MIN_GAP_MS,
            max_gap_ms=MAX_GAP_MS,
            min_avg_gap_ms=MIN_AVG_GAP_MS,
            max_avg_gap_ms=MAX_AVG_GAP_MS,
            validation_errors="\n".join(f"- {e}" for e in errors),
            original_plan=str(plan),
        )

    def _compute_fallback(
        self,
        dialogues: List[Dict[str, Any]],
        scene_context_raw: Dict[str, Any],
    ) -> TimingPlan:
        """Compute timing using pure rule-based fallback."""
        dialogue_contexts = build_dialogue_contexts(dialogues)
        scene_context = build_scene_context(
            scene_id=scene_context_raw.get("scene_id", 0),
            scene_number=scene_context_raw.get("scene_number", 1),
            dialogues=dialogues,
            conflict_notes=scene_context_raw.get("conflict_notes"),
        )

        decisions = calculate_fallback_timing(dialogue_contexts, scene_context)
        total_gap = sum(d.adjusted_duration_ms for d in decisions)
        avg_gap = total_gap / len(decisions) if decisions else 0

        return TimingPlan(
            scene_id=scene_context.scene_id,
            decisions=decisions,
            total_gap_ms=total_gap,
            avg_gap_ms=avg_gap,
            rhythm_score=calculate_rhythm_score(decisions),
            reasoning_summary="fallback_rule_based_timing",
            fallback_used=True,
        )

    def _classify_failure_mode(self, error: AgentError) -> FailureMode:
        """Classify error into failure mode for monitoring."""
        if error.error_type == AgentErrorType.SYNTAX:
            return FailureMode.JSON_PARSE
        if error.error_type == AgentErrorType.VALIDATION:
            return FailureMode.CONTENT_CONSTRAINT
        if error.error_type == AgentErrorType.NETWORK:
            return FailureMode.API_ERROR
        return FailureMode.UNKNOWN
