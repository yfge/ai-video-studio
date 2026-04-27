"""Validation and result-formatting nodes for StoryboardPipeline."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from app.services.storyboard.pipeline.pipeline_context import PipelineContext
from app.services.storyboard.pipeline.pipeline_state import (
    PipelinePhase,
    PipelineState,
    ValidationResult,
)


class StoryboardPipelineValidationMixin:
    """Validation, recovery, finalization, and result formatting nodes."""

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

    def _node_validate_frames(self, state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Frame validation node."""
        ps: PipelineState = state_dict["pipeline_state"]
        ctx: PipelineContext = state_dict["context"]
        ps.phase = PipelinePhase.VALIDATE_FRAMES
        for name in ["frame_integrity", "character_presence", "cinematic_rules"]:
            for result in self.validators[name].validate(ps, ctx):
                ps.add_validation(result)
        ps.add_reasoning("frames_validated")
        return state_dict

    def _node_validate_timeline(self, state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Timeline validation node."""
        ps: PipelineState = state_dict["pipeline_state"]
        ctx: PipelineContext = state_dict["context"]
        ps.phase = PipelinePhase.VALIDATE_TIMELINE
        for result in self.validators["timeline"].validate(ps, ctx):
            ps.add_validation(result)
        ps.add_reasoning("timeline_validated")
        return state_dict

    def _node_recovery(self, state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Recovery node."""
        ps: PipelineState = state_dict["pipeline_state"]
        ctx: PipelineContext = state_dict["context"]
        ps.phase = PipelinePhase.RECOVERY
        result = self.repair.repair(ps, ctx)
        ps.record_recovery("incremental_repair", result.to_dict())
        ps.validation_results = []
        ps.has_errors = False
        ps.has_warnings = False
        ps.add_reasoning(f"recovery_{result.success}")
        return state_dict

    def _node_finalize(self, state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Finalization node."""
        ps: PipelineState = state_dict["pipeline_state"]
        ps.phase = PipelinePhase.FAILED if ps.has_errors else PipelinePhase.COMPLETED
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
            "usage": ps.usage,
            "plan": ps.plan,
            "agent_kind": "storyboard_pipeline",
            "graph_name": "storyboard_pipeline",
            "graph_version": "2026-04-27",
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
