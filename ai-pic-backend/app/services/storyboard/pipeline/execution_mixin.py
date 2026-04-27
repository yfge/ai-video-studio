"""Execution helpers for StoryboardPipeline."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, Optional

from app.services.storyboard.pipeline.pipeline_context import PipelineContext
from app.services.storyboard.pipeline.pipeline_state import PipelinePhase, PipelineState

try:
    from langgraph.graph import END, StateGraph
except ImportError:  # pragma: no cover - guarded by caller
    END = "__end__"
    StateGraph = None  # type: ignore[assignment]

if TYPE_CHECKING:
    from app.models.script import Episode, Script


class StoryboardPipelineExecutionMixin:
    """LangGraph and sequential execution methods for StoryboardPipeline."""

    async def _execute_langgraph(
        self,
        state: PipelineState,
        context: PipelineContext,
        script: "Script",
        episode: Optional["Episode"],
    ) -> Dict[str, Any]:
        """Execute pipeline using LangGraph."""
        graph = StateGraph(dict)

        graph.add_node("precheck", self._node_precheck)
        graph.add_node("generate_plan", self._node_generate_plan)
        graph.add_node("validate_plan", self._node_validate_plan)
        graph.add_node("generate_frames", self._node_generate_frames)
        graph.add_node("validate_frames", self._node_validate_frames)
        graph.add_node("validate_timeline", self._node_validate_timeline)
        graph.add_node("recovery", self._node_recovery)
        graph.add_node("finalize", self._node_finalize)
        graph.set_entry_point("precheck")

        def route_after_precheck(s: Dict[str, Any]) -> str:
            ps = s.get("pipeline_state")
            return "finalize" if getattr(ps, "has_errors", False) else "generate_plan"

        def route_after_generate_plan(s: Dict[str, Any]) -> str:
            ps = s.get("pipeline_state")
            return "finalize" if getattr(ps, "has_errors", False) else "validate_plan"

        def route_after_validate_plan(s: Dict[str, Any]) -> str:
            ps = s.get("pipeline_state")
            return "finalize" if getattr(ps, "has_errors", False) else "generate_frames"

        graph.add_conditional_edges(
            "precheck",
            route_after_precheck,
            {"generate_plan": "generate_plan", "finalize": "finalize"},
        )
        graph.add_conditional_edges(
            "generate_plan",
            route_after_generate_plan,
            {"validate_plan": "validate_plan", "finalize": "finalize"},
        )
        graph.add_conditional_edges(
            "validate_plan",
            route_after_validate_plan,
            {"generate_frames": "generate_frames", "finalize": "finalize"},
        )
        graph.add_edge("generate_frames", "validate_frames")
        graph.add_edge("validate_frames", "validate_timeline")

        def route_after_timeline(s: Dict[str, Any]) -> str:
            ps = s.get("pipeline_state")
            if isinstance(ps, PipelineState) and ps.has_errors and ps.can_recover():
                return "recovery"
            return "finalize"

        graph.add_conditional_edges("validate_timeline", route_after_timeline)
        graph.add_edge("recovery", "validate_frames")
        graph.add_edge("finalize", END)

        compiled = graph.compile()
        result = await compiled.ainvoke(
            {
                "pipeline_state": state,
                "context": context,
                "script": script,
                "episode": episode,
            }
        )
        return self._format_result(result)

    async def _execute_sequential(
        self,
        state: PipelineState,
        context: PipelineContext,
        script: "Script",
        episode: Optional["Episode"],
    ) -> Dict[str, Any]:
        """Execute pipeline sequentially without LangGraph."""
        self.logger.info("Executing storyboard pipeline sequentially")

        state.phase = PipelinePhase.PRECHECK
        state.add_reasoning("precheck_started")
        precheck_result = self.precheck.check_from_context(context)
        if not precheck_result.ready:
            state.phase = PipelinePhase.FAILED
            return self._format_error(state, precheck_result.message)
        state.add_reasoning("precheck_passed")

        state.phase = PipelinePhase.VALIDATE_PLAN
        consistency_results = self.validators["consistency"].validate(state, context)
        for result in consistency_results:
            state.add_validation(result)
        state.add_reasoning("consistency_validated")

        state.phase = PipelinePhase.GENERATE_FRAMES
        if self.ai_service:
            state.frames = await self._generate_frames_via_service(
                state, context, script
            )
        state.add_reasoning(f"generated_{len(state.frames)}_frames")

        state.phase = PipelinePhase.VALIDATE_FRAMES
        for name in ["frame_integrity", "character_presence", "cinematic_rules"]:
            for result in self.validators[name].validate(state, context):
                state.add_validation(result)
        state.add_reasoning("frames_validated")

        state.phase = PipelinePhase.VALIDATE_TIMELINE
        for result in self.validators["timeline"].validate(state, context):
            state.add_validation(result)
        state.add_reasoning("timeline_validated")

        if state.has_errors and state.can_recover():
            state.phase = PipelinePhase.RECOVERY
            repair_result = self.repair.repair(state, context)
            state.record_recovery("incremental_repair", repair_result.to_dict())
            state.add_reasoning(f"repair_attempted_{repair_result.success}")
            state.validation_results = []
            state.has_errors = False
            for validator in self.validators.values():
                for result in validator.validate(state, context):
                    state.add_validation(result)

        state.phase = (
            PipelinePhase.FINALIZE if not state.has_errors else PipelinePhase.FAILED
        )
        state.completed_at = datetime.now(timezone.utc)
        return self._format_result({"pipeline_state": state, "context": context})
