"""
LangGraph-based Timeline Agent for intelligent gap calculation.

Implements a ReAct-style agent that analyzes scene context,
reasons about timing, and produces validated timing plans.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

from app.core.logging import get_logger
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

try:
    from langgraph.graph import END, StateGraph

    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False

if TYPE_CHECKING:
    from app.services.ai_service import AIService


class TimelineLangGraphAgent:
    """LangGraph-based agent for intelligent timeline gap calculation."""

    def __init__(self, service: "AIService") -> None:
        """Initialize with AI service reference."""
        self.service = service
        self.logger = get_logger()

    async def compute_timing(
        self,
        *,
        dialogues: list[dict[str, Any]],
        stage_directions: list[dict[str, Any]],
        scene_context: dict[str, Any],
        model: Optional[str] = None,
        prefer_provider: Optional[str] = None,
        temperature: float = 0.4,
        target_duration_seconds: Optional[int] = None,
    ) -> Optional[TimingPlan]:
        """
        Main entry point for computing intelligent timing.

        Args:
            target_duration_seconds: Optional target scene duration in seconds.
                When provided, the agent will try to allocate gaps to match
                the target duration.

        Returns TimingPlan or None if agent unavailable.
        Falls back to rule-based timing on LLM failure.
        """
        if not LANGGRAPH_AVAILABLE:
            self.logger.warning("LangGraph not available, using fallback")
            return self._compute_fallback(dialogues, scene_context)

        if not self.service.ai_manager:
            self.logger.warning("AI manager not available, using fallback")
            return self._compute_fallback(dialogues, scene_context)

        # Build the graph
        graph = self._build_graph(model, prefer_provider, temperature)
        app = graph.compile()

        # Prepare initial state
        initial_state = {
            "dialogues": dialogues,
            "stage_directions": stage_directions,
            "scene_context_raw": scene_context,
            "reasoning": [],
            "model": model,
            "prefer_provider": prefer_provider,
            "temperature": temperature,
            "target_duration_seconds": target_duration_seconds,
        }

        try:
            result = await app.ainvoke(initial_state)
            if result.get("final_plan"):
                return TimingPlan.model_validate(result["final_plan"])
        except Exception as e:
            self.logger.error(f"Timeline agent failed: {e}")

        return self._compute_fallback(dialogues, scene_context)

    def _build_graph(
        self,
        model: Optional[str],
        prefer_provider: Optional[str],
        temperature: float,
    ) -> "StateGraph":
        """Build the LangGraph state machine."""
        graph = StateGraph(dict)

        # --- Node definitions ---
        graph.add_node("analyze_scene", self._analyze_scene)
        graph.add_node(
            "think_timing", self._make_think_timing(model, prefer_provider, temperature)
        )
        graph.add_node("propose_gaps", self._propose_gaps)
        graph.add_node("validate_rhythm", self._validate_rhythm)
        graph.add_node(
            "adjust_timing", self._make_adjust_timing(model, prefer_provider)
        )
        graph.add_node("finalize", self._finalize)

        # --- Edges ---
        graph.set_entry_point("analyze_scene")
        graph.add_edge("analyze_scene", "think_timing")
        graph.add_edge("think_timing", "propose_gaps")
        graph.add_edge("propose_gaps", "validate_rhythm")
        graph.add_conditional_edges(
            "validate_rhythm",
            self._route_validation,
            {"finalize": "finalize", "adjust_timing": "adjust_timing"},
        )
        graph.add_edge("adjust_timing", "validate_rhythm")
        graph.add_edge("finalize", END)

        return graph

    def _analyze_scene(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract scene context and prepare dialogue contexts."""
        dialogues = state.get("dialogues", [])
        scene_ctx_raw = state.get("scene_context_raw", {})

        # Build structured contexts with enhanced scene data
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

        reasoning = state.get("reasoning", []) + [
            f"analyzed: mood={scene_context.mood}, conflict={scene_context.conflict_level}, "
            f"location={scene_context.location or 'unknown'}"
        ]

        return {
            **state,
            "scene_context": scene_context.model_dump(),
            "dialogue_contexts": [c.model_dump() for c in dialogue_contexts],
            "reasoning": reasoning,
        }

    def _make_think_timing(
        self,
        model: Optional[str],
        prefer_provider: Optional[str],
        temperature: float,
    ):
        """Create think_timing node with closure over LLM params."""

        async def think_timing(state: Dict[str, Any]) -> Dict[str, Any]:
            scene_ctx = state.get("scene_context", {})
            dialogue_contexts = state.get("dialogue_contexts", [])
            target_duration = state.get("target_duration_seconds")

            # Build prompt with optional target duration
            prompt = self._build_reasoning_prompt(
                scene_ctx, dialogue_contexts, target_duration
            )

            try:
                resp = await self.service.ai_manager.generate_text(
                    prompt=prompt,
                    temperature=temperature,
                    model=model,
                    prefer_provider=prefer_provider,
                    json_schema={
                        "name": "timeline_timing",
                        "schema": TIMING_OUTPUT_SCHEMA,
                    },
                    system_prompt=TIMELINE_SYSTEM_PROMPT,
                )
                content = (
                    resp.data if isinstance(resp.data, str) else str(resp.data or "")
                )
                return {
                    **state,
                    "raw_llm_output": content,
                    "provider_used": resp.provider,
                    "model_used": resp.model,
                    "reasoning": state.get("reasoning", [])
                    + ["llm_reasoning_complete"],
                }
            except Exception as e:
                self.logger.warning(f"LLM call failed: {e}")
                return {
                    **state,
                    "raw_llm_output": None,
                    "reasoning": state.get("reasoning", []) + [f"llm_failed: {e}"],
                }

        return think_timing

    def _propose_gaps(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM output into structured timing plan."""
        raw_output = state.get("raw_llm_output", "")
        scene_ctx = state.get("scene_context", {})

        if not raw_output:
            return {
                **state,
                "proposed_plan": None,
                "reasoning": state.get("reasoning", []) + ["no_llm_output"],
            }

        parsed = extract_json_block(raw_output)
        if not parsed:
            return {
                **state,
                "proposed_plan": None,
                "reasoning": state.get("reasoning", []) + ["parse_failed"],
            }

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

        total_gap = sum(d.adjusted_duration_ms for d in decisions)
        avg_gap = total_gap / len(decisions) if decisions else 0
        rhythm_score = calculate_rhythm_score(decisions)

        proposed_plan = TimingPlan(
            scene_id=scene_ctx.get("scene_id", 0),
            decisions=decisions,
            total_gap_ms=total_gap,
            avg_gap_ms=avg_gap,
            rhythm_score=rhythm_score,
            reasoning_summary=parsed.get("overall_rhythm_note", ""),
        )

        return {
            **state,
            "proposed_plan": proposed_plan.model_dump(),
            "reasoning": state.get("reasoning", []) + ["plan_proposed"],
        }

    def _validate_rhythm(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Validate timing plan against constraints."""
        plan = state.get("proposed_plan")
        errors = []

        if not plan:
            return {
                **state,
                "validation_passed": False,
                "validation_errors": ["no_plan_to_validate"],
            }

        decisions = plan.get("decisions", [])

        for d in decisions:
            dur = d.get("adjusted_duration_ms", 0)
            idx = d.get("segment_index", 0)
            if dur < MIN_GAP_MS:
                errors.append(f"gap_{idx}_too_short: {dur}ms < {MIN_GAP_MS}ms")
            if dur > MAX_GAP_MS:
                errors.append(f"gap_{idx}_too_long: {dur}ms > {MAX_GAP_MS}ms")

        avg_gap = plan.get("avg_gap_ms", 0)
        if avg_gap < MIN_AVG_GAP_MS:
            errors.append(f"avg_gap_too_short: {avg_gap:.0f}ms")
        if avg_gap > MAX_AVG_GAP_MS:
            errors.append(f"avg_gap_too_long: {avg_gap:.0f}ms")

        # Check for monotonous rhythm
        if len(decisions) > 3:
            durations = [d.get("adjusted_duration_ms", 0) for d in decisions]
            if len(set(durations)) == 1:
                errors.append("rhythm_too_monotonous")

        # Duration validation against target
        target_duration_seconds = state.get("target_duration_seconds")
        if target_duration_seconds:
            total_gap_ms = plan.get("total_gap_ms", 0)
            # Calculate total duration: dialogue durations + gaps
            # Prefer actual_duration_ms (from TTS) over estimated_duration_ms
            dialogue_contexts = state.get("dialogue_contexts", [])
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

            self.logger.info(
                "Timeline Agent duration validation",
                extra={
                    "target_duration_seconds": target_duration_seconds,
                    "dialogue_duration_ms": dialogue_duration_ms,
                    "total_gap_ms": total_gap_ms,
                    "computed_total_ms": computed_total_ms,
                    "duration_ratio": round(duration_ratio, 2),
                    "using_actual_durations": has_actual_durations,
                },
            )

            # Use tighter tolerance (±20%) when using actual TTS durations
            # Use wider tolerance (±40%) when using estimated durations
            if has_actual_durations:
                tolerance_low, tolerance_high = 0.8, 1.2
            else:
                tolerance_low, tolerance_high = 0.6, 1.4

            # NOTE: 目标时长对齐的“补足”由 audio segment padding 负责（见 segment_padding.py），
            # Timeline Agent 只负责节奏合理的间隔计算；因此不把“时长不足”视为硬错误，
            # 否则在对白数量较少的场景下会出现不可满足的约束并触发无意义的修复循环。
            if duration_ratio > tolerance_high:
                errors.append(
                    f"duration_too_long: {computed_total_ms}ms vs target {target_ms}ms "
                    f"({duration_ratio:.0%})"
                )

        return {
            **state,
            "validation_passed": len(errors) == 0,
            "validation_errors": errors,
        }

    def _route_validation(self, state: Dict[str, Any]) -> str:
        """Route based on validation result."""
        if state.get("validation_passed"):
            return "finalize"
        if state.get("repair_attempts", 0) >= MAX_REPAIR_ATTEMPTS:
            return "finalize"
        return "adjust_timing"

    def _make_adjust_timing(self, model: Optional[str], prefer_provider: Optional[str]):
        """Create adjust_timing node with LLM repair."""

        async def adjust_timing(state: Dict[str, Any]) -> Dict[str, Any]:
            repair_attempts = state.get("repair_attempts", 0) + 1
            errors = state.get("validation_errors", [])
            plan = state.get("proposed_plan", {})

            repair_prompt = TIMELINE_REPAIR_PROMPT.format(
                min_gap_ms=MIN_GAP_MS,
                max_gap_ms=MAX_GAP_MS,
                min_avg_gap_ms=MIN_AVG_GAP_MS,
                max_avg_gap_ms=MAX_AVG_GAP_MS,
                validation_errors="\n".join(f"- {e}" for e in errors),
                original_plan=str(plan),
            )

            try:
                resp = await self.service.ai_manager.generate_text(
                    prompt=repair_prompt,
                    temperature=0.3,
                    model=model,
                    prefer_provider=prefer_provider,
                    json_schema={
                        "name": "timeline_timing_repair",
                        "schema": TIMING_OUTPUT_SCHEMA,
                    },
                    system_prompt=TIMELINE_SYSTEM_PROMPT,
                )
                content = (
                    resp.data if isinstance(resp.data, str) else str(resp.data or "")
                )
                return {
                    **state,
                    "raw_llm_output": content,
                    "repair_attempts": repair_attempts,
                    "reasoning": state.get("reasoning", [])
                    + [f"repair_attempt_{repair_attempts}"],
                }
            except Exception as e:
                self.logger.warning(f"Repair LLM call failed: {e}")
                return {
                    **state,
                    "raw_llm_output": None,
                    "repair_attempts": repair_attempts,
                }

        return adjust_timing

    def _finalize(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare final output with fallback if needed."""
        if state.get("validation_passed") and state.get("proposed_plan"):
            return {
                **state,
                "final_plan": state["proposed_plan"],
            }

        # Use fallback
        return self._apply_fallback_to_state(state)

    def _apply_fallback_to_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Apply rule-based fallback timing."""
        from .schemas import DialogueContext, SceneContext

        dialogue_dicts = state.get("dialogue_contexts", [])
        scene_dict = state.get("scene_context", {})

        dialogue_contexts = [DialogueContext.model_validate(d) for d in dialogue_dicts]
        scene_context = SceneContext.model_validate(scene_dict)

        decisions = calculate_fallback_timing(dialogue_contexts, scene_context)
        total_gap = sum(d.adjusted_duration_ms for d in decisions)
        avg_gap = total_gap / len(decisions) if decisions else 0

        fallback_plan = TimingPlan(
            scene_id=scene_context.scene_id,
            decisions=decisions,
            total_gap_ms=total_gap,
            avg_gap_ms=avg_gap,
            rhythm_score=calculate_rhythm_score(decisions),
            reasoning_summary="fallback_rule_based_timing",
            fallback_used=True,
        )

        return {
            **state,
            "final_plan": fallback_plan.model_dump(),
            "reasoning": state.get("reasoning", []) + ["finalized_with_fallback"],
        }

    def _compute_fallback(
        self,
        dialogues: list[dict[str, Any]],
        scene_context_raw: dict[str, Any],
    ) -> TimingPlan:
        """Compute timing using pure fallback (no LangGraph)."""
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
            reasoning_summary="pure_fallback_no_langgraph",
            fallback_used=True,
        )

    def _build_reasoning_prompt(
        self,
        scene_context: dict[str, Any],
        dialogue_contexts: list[dict[str, Any]],
        target_duration_seconds: Optional[int] = None,
    ) -> str:
        """Build the reasoning prompt for LLM."""
        from .schemas import DialogueContext

        contexts = [DialogueContext.model_validate(d) for d in dialogue_contexts]
        formatted = format_dialogue_for_prompt(contexts)

        # Calculate total dialogue duration from actual/estimated durations
        total_dialogue_ms = sum(
            (c.actual_duration_ms or c.estimated_duration_ms or 0) for c in contexts
        )
        has_actual_durations = any(c.actual_duration_ms for c in contexts)

        # Build enhanced scene info
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
- 停顿时长需要合理分配，使得整体场景（对白 + 停顿 + 动作）接近目标时长
- 如果对白本身时长不足，适当增加停顿时间来补充
- 但停顿时间仍需要自然合理，不能过于冗长
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
1. 情绪过渡（愤怒→平静需要更长停顿）
2. 戏剧节奏（高冲突场景需要更短停顿保持紧张感）
3. 语义完整性（句号后比逗号停顿更长）
4. 角色切换（不同角色之间需要呼吸空间）
5. 场景氛围（夜晚场景可能需要更长的呼吸空间）
{f"6. 时长约束（总时长需接近目标 {target_duration_seconds} 秒）" if target_duration_seconds else ""}

输出 JSON 格式的 timing_decisions。"""
