"""
Main LangGraph pipeline for storyboard generation with React validation.

Orchestrates the complete storyboard generation workflow:
precheck → sync → plan → validate → generate → validate → finalize
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, Optional

from app.core.logging import get_logger
from app.services.storyboard.pipeline.pipeline_context import (
    PipelineContext,
    build_pipeline_context,
)
from app.services.storyboard.pipeline.pipeline_state import (
    PipelinePhase,
    PipelineState,
    ValidationResult,
)
from app.services.storyboard.recovery.incremental_repair import IncrementalRepair
from app.services.storyboard.recovery.retry_strategy import RetryStrategy
from app.services.storyboard.sync.data_precheck import DataPrecheck
from app.services.storyboard.validators import (
    CharacterPresenceValidator,
    ConsistencyValidator,
    FrameIntegrityValidator,
    TimelineValidator,
)

try:
    from langgraph.graph import END, StateGraph

    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.models.script import Episode, Script
    from app.services.ai_service import AIService


class StoryboardPipeline:
    """
    LangGraph-based storyboard generation pipeline with React validation.

    Pipeline stages:
    1. precheck - Validate data availability
    2. sync_structure - Reconcile Script JSON with story_structure
    3. generate_plan - Create storyboard plan
    4. validate_plan - ConsistencyValidator
    5. generate_frames - Generate storyboard frames
    6. validate_frames - FrameIntegrityValidator + CharacterPresenceValidator
    7. validate_timeline - TimelineValidator
    8. recovery - Repair issues if needed
    9. finalize - Persist results
    """

    def __init__(
        self,
        db: "Session",
        ai_service: Optional["AIService"] = None,
    ):
        self.db = db
        self.ai_service = ai_service
        self.logger = get_logger()

        # Initialize components
        self.precheck = DataPrecheck(db)
        self.retry_strategy = RetryStrategy()
        self.repair = IncrementalRepair()

        # Initialize validators
        self.validators = {
            "consistency": ConsistencyValidator(),
            "timeline": TimelineValidator(),
            "frame_integrity": FrameIntegrityValidator(),
            "character_presence": CharacterPresenceValidator(),
        }

    async def generate(
        self,
        *,
        script: "Script",
        episode: Optional["Episode"] = None,
        frames_per_scene: int = 4,
        selected_scenes: Optional[list[int]] = None,
        model: Optional[str] = None,
        prefer_provider: Optional[str] = None,
        temperature: float = 0.7,
        max_frames: Optional[int] = None,
        use_langgraph: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute the storyboard generation pipeline.

        Args:
            script: Script model instance
            episode: Optional Episode for audio-based generation
            frames_per_scene: Target frames per scene
            selected_scenes: Optional list of scene numbers to generate
            model: AI model to use
            prefer_provider: Preferred AI provider
            temperature: Generation temperature
            max_frames: Maximum total frames
            use_langgraph: Whether to use LangGraph orchestration

        Returns:
            Dictionary with generated frames and metadata
        """
        # Build context
        context = build_pipeline_context(
            self.db,
            script=script,
            episode=episode,
        )

        # Initialize state
        state = PipelineState(
            script_id=script.id,
            episode_id=episode.id if episode else None,
            frames_per_scene=frames_per_scene,
            selected_scenes=selected_scenes,
            temperature=temperature,
        )

        if use_langgraph and LANGGRAPH_AVAILABLE:
            return await self._execute_langgraph(state, context, script, episode)
        else:
            return await self._execute_sequential(state, context, script, episode)

    async def _execute_langgraph(
        self,
        state: PipelineState,
        context: PipelineContext,
        script: "Script",
        episode: Optional["Episode"],
    ) -> Dict[str, Any]:
        """Execute pipeline using LangGraph."""
        graph = StateGraph(dict)

        # Define nodes
        graph.add_node("precheck", self._node_precheck)
        graph.add_node("validate_plan", self._node_validate_plan)
        graph.add_node("generate_frames", self._node_generate_frames)
        graph.add_node("validate_frames", self._node_validate_frames)
        graph.add_node("validate_timeline", self._node_validate_timeline)
        graph.add_node("recovery", self._node_recovery)
        graph.add_node("finalize", self._node_finalize)

        # Define edges
        graph.set_entry_point("precheck")
        graph.add_edge("precheck", "validate_plan")
        graph.add_edge("validate_plan", "generate_frames")
        graph.add_edge("generate_frames", "validate_frames")
        graph.add_edge("validate_frames", "validate_timeline")

        # Conditional routing for recovery
        def route_after_timeline(s: Dict[str, Any]) -> str:
            ps = s.get("pipeline_state")
            if isinstance(ps, PipelineState) and ps.has_errors and ps.can_recover():
                return "recovery"
            return "finalize"

        graph.add_conditional_edges("validate_timeline", route_after_timeline)
        graph.add_edge("recovery", "validate_frames")
        graph.add_edge("finalize", END)

        # Execute
        compiled = graph.compile()
        initial = {
            "pipeline_state": state,
            "context": context,
            "script": script,
            "episode": episode,
        }
        result = await compiled.ainvoke(initial)
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

        # Precheck
        state.phase = PipelinePhase.PRECHECK
        state.add_reasoning("precheck_started")
        precheck_result = self.precheck.check_from_context(context)
        if not precheck_result.ready:
            state.phase = PipelinePhase.FAILED
            return self._format_error(state, precheck_result.message)
        state.add_reasoning("precheck_passed")

        # Validate consistency
        state.phase = PipelinePhase.VALIDATE_PLAN
        consistency_results = self.validators["consistency"].validate(state, context)
        for r in consistency_results:
            state.add_validation(r)
        state.add_reasoning("consistency_validated")

        # Generate frames (delegate to existing service)
        state.phase = PipelinePhase.GENERATE_FRAMES
        if self.ai_service:
            frames = await self._generate_frames_via_service(state, context, script)
            state.frames = frames
        state.add_reasoning(f"generated_{len(state.frames)}_frames")

        # Validate frames
        state.phase = PipelinePhase.VALIDATE_FRAMES
        for validator_name in ["frame_integrity", "character_presence"]:
            results = self.validators[validator_name].validate(state, context)
            for r in results:
                state.add_validation(r)
        state.add_reasoning("frames_validated")

        # Validate timeline
        state.phase = PipelinePhase.VALIDATE_TIMELINE
        timeline_results = self.validators["timeline"].validate(state, context)
        for r in timeline_results:
            state.add_validation(r)
        state.add_reasoning("timeline_validated")

        # Recovery if needed
        if state.has_errors and state.can_recover():
            state.phase = PipelinePhase.RECOVERY
            repair_result = self.repair.repair(state, context)
            state.record_recovery("incremental_repair", repair_result.to_dict())
            state.add_reasoning(f"repair_attempted_{repair_result.success}")

            # Re-validate after repair
            state.validation_results = []
            state.has_errors = False
            for validator in self.validators.values():
                for r in validator.validate(state, context):
                    state.add_validation(r)

        # Finalize
        state.phase = PipelinePhase.FINALIZE if not state.has_errors else PipelinePhase.FAILED
        state.completed_at = datetime.now(timezone.utc)

        return self._format_result({"pipeline_state": state, "context": context})

    async def _generate_frames_via_service(
        self,
        state: PipelineState,
        context: PipelineContext,
        script: "Script",
    ) -> list[Dict[str, Any]]:
        """Generate frames using AIService."""
        if not self.ai_service:
            return []

        # Build script dict for service
        script_dict = {
            "id": script.id,
            "content": script.content,
            "scenes": script.scenes,
            "dialogues": script.dialogues,
        }

        # Use existing storyboard generation
        result = await self.ai_service.generate_storyboard(
            script=script_dict,
            frames_per_scene=state.frames_per_scene,
            selected_scenes=state.selected_scenes,
            temperature=state.temperature,
        )

        if result and "frames" in result:
            return result["frames"]

        # Try parsing from content
        if result and result.get("content"):
            import json
            try:
                parsed = json.loads(result["content"])
                return parsed.get("frames", [])
            except json.JSONDecodeError:
                pass

        return []

    # Node implementations for LangGraph

    def _node_precheck(self, state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Precheck node."""
        ps: PipelineState = state_dict["pipeline_state"]
        ctx: PipelineContext = state_dict["context"]

        ps.phase = PipelinePhase.PRECHECK
        ps.add_reasoning("precheck_started")

        result = self.precheck.check_from_context(ctx)
        if not result.ready:
            ps.add_validation(
                ValidationResult.critical(
                    validator_name="precheck",
                    message=result.message,
                    details={"errors": result.errors},
                )
            )

        ps.add_reasoning("precheck_completed")
        return state_dict

    def _node_validate_plan(self, state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Plan validation node."""
        ps: PipelineState = state_dict["pipeline_state"]
        ctx: PipelineContext = state_dict["context"]

        ps.phase = PipelinePhase.VALIDATE_PLAN
        results = self.validators["consistency"].validate(ps, ctx)
        for r in results:
            ps.add_validation(r)
        ps.add_reasoning("plan_validated")
        return state_dict

    async def _node_generate_frames(self, state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Frame generation node."""
        ps: PipelineState = state_dict["pipeline_state"]
        ctx: PipelineContext = state_dict["context"]
        script = state_dict.get("script")

        ps.phase = PipelinePhase.GENERATE_FRAMES
        if self.ai_service and script:
            frames = await self._generate_frames_via_service(ps, ctx, script)
            ps.frames = frames
        ps.add_reasoning(f"generated_{len(ps.frames)}_frames")
        return state_dict

    def _node_validate_frames(self, state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Frame validation node."""
        ps: PipelineState = state_dict["pipeline_state"]
        ctx: PipelineContext = state_dict["context"]

        ps.phase = PipelinePhase.VALIDATE_FRAMES
        for name in ["frame_integrity", "character_presence"]:
            for r in self.validators[name].validate(ps, ctx):
                ps.add_validation(r)
        ps.add_reasoning("frames_validated")
        return state_dict

    def _node_validate_timeline(self, state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Timeline validation node."""
        ps: PipelineState = state_dict["pipeline_state"]
        ctx: PipelineContext = state_dict["context"]

        ps.phase = PipelinePhase.VALIDATE_TIMELINE
        for r in self.validators["timeline"].validate(ps, ctx):
            ps.add_validation(r)
        ps.add_reasoning("timeline_validated")
        return state_dict

    def _node_recovery(self, state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Recovery node."""
        ps: PipelineState = state_dict["pipeline_state"]
        ctx: PipelineContext = state_dict["context"]

        ps.phase = PipelinePhase.RECOVERY
        result = self.repair.repair(ps, ctx)
        ps.record_recovery("incremental_repair", result.to_dict())

        # Clear validation state for re-validation
        ps.validation_results = []
        ps.has_errors = False
        ps.has_warnings = False
        ps.add_reasoning(f"recovery_{result.success}")
        return state_dict

    def _node_finalize(self, state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Finalization node."""
        ps: PipelineState = state_dict["pipeline_state"]

        if ps.has_errors:
            ps.phase = PipelinePhase.FAILED
        else:
            ps.phase = PipelinePhase.COMPLETED

        ps.completed_at = datetime.now(timezone.utc)
        ps.add_reasoning("finalized")
        return state_dict

    def _format_result(self, state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Format pipeline result for return."""
        ps: PipelineState = state_dict.get("pipeline_state")
        if not ps:
            return {"error": "pipeline_state_missing"}

        return {
            "success": ps.phase == PipelinePhase.COMPLETED,
            "frames": ps.frames,
            "frame_count": len(ps.frames),
            "phase": ps.phase.value,
            "validation_results": [v.to_dict() for v in ps.validation_results],
            "has_errors": ps.has_errors,
            "has_warnings": ps.has_warnings,
            "reasoning_trace": ps.reasoning_trace,
            "recovery_history": ps.recovery_history,
            "provider_used": ps.provider_used,
            "model_used": ps.model_used,
            "started_at": ps.started_at.isoformat(),
            "completed_at": ps.completed_at.isoformat() if ps.completed_at else None,
        }

    def _format_error(self, state: PipelineState, message: str) -> Dict[str, Any]:
        """Format error result."""
        state.completed_at = datetime.now(timezone.utc)
        return {
            "success": False,
            "error": message,
            "frames": [],
            "phase": state.phase.value,
            "reasoning_trace": state.reasoning_trace,
        }


__all__ = ["StoryboardPipeline", "LANGGRAPH_AVAILABLE"]
