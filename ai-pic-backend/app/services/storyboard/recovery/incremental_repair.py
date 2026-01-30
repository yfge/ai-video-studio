"""
Incremental repair for partial generation failures.

Provides capabilities to repair partially generated storyboards
without regenerating everything from scratch.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.storyboard.pipeline.pipeline_context import PipelineContext
    from app.services.storyboard.pipeline.pipeline_state import (
        PipelineState,
        ValidationResult,
    )


@dataclass
class RepairResult:
    """Result of a repair operation."""

    success: bool
    message: str
    frames_repaired: int = 0
    frames_regenerated: int = 0
    issues_fixed: list[str] = field(default_factory=list)
    issues_remaining: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "message": self.message,
            "frames_repaired": self.frames_repaired,
            "frames_regenerated": self.frames_regenerated,
            "issues_fixed": self.issues_fixed,
            "issues_remaining": self.issues_remaining,
        }


class IncrementalRepair:
    """
    Incremental repair capabilities for storyboard generation.

    Analyzes validation failures and applies targeted fixes:
    - Fill missing frame fields
    - Regenerate specific scenes
    - Fix timeline issues
    - Correct frame numbering
    """

    def __init__(self):
        self.repair_handlers: dict[str, Any] = {
            "timeline_validator": self._repair_timeline_issues,
            "frame_integrity_validator": self._repair_frame_integrity,
            "consistency_validator": self._repair_consistency_issues,
        }

    def analyze_failures(
        self,
        state: "PipelineState",
    ) -> dict[str, list["ValidationResult"]]:
        """
        Analyze failed validations and group by repair strategy.

        Returns dict of validator_name -> list of failures.
        """
        failures_by_validator: dict[str, list["ValidationResult"]] = {}

        for result in state.get_failed_validations():
            validator = result.validator_name
            failures_by_validator.setdefault(validator, []).append(result)

        return failures_by_validator

    def repair(
        self,
        state: "PipelineState",
        context: "PipelineContext",
    ) -> RepairResult:
        """
        Attempt to repair issues in the current state.

        Args:
            state: Current pipeline state with frames and validation results
            context: Pipeline context with script/scene data

        Returns:
            RepairResult with details of what was fixed
        """
        result = RepairResult(success=True, message="")

        failures = self.analyze_failures(state)
        if not failures:
            result.message = "No failures to repair"
            return result

        # Apply repairs for each validator type
        for validator_name, issues in failures.items():
            handler = self.repair_handlers.get(validator_name)
            if handler:
                fixed, remaining = handler(state, context, issues)
                result.issues_fixed.extend(fixed)
                result.issues_remaining.extend(remaining)

        # Apply auto-fixes from validators
        result = self._apply_auto_fixes(state, context, result)

        result.frames_repaired = len(result.issues_fixed)
        result.success = len(result.issues_remaining) == 0

        if result.success:
            result.message = f"Repaired {result.frames_repaired} issues"
        else:
            result.message = (
                f"Repaired {result.frames_repaired}, "
                f"{len(result.issues_remaining)} remaining"
            )

        return result

    def _repair_timeline_issues(
        self,
        state: "PipelineState",
        context: "PipelineContext",
        issues: list["ValidationResult"],
    ) -> tuple[list[str], list[str]]:
        """Repair timeline-related issues."""
        fixed: list[str] = []
        remaining: list[str] = []

        for issue in issues:
            if "duration" in issue.message.lower():
                # Fix duration inconsistencies
                self._fix_duration_inconsistencies(state.frames)
                fixed.append(f"Fixed duration inconsistencies: {issue.message}")
            elif "gap" in issue.message.lower():
                # Gaps require frame regeneration
                remaining.append(f"Timeline gap requires regeneration: {issue.message}")
            elif "overlap" in issue.message.lower():
                # Overlaps might be fixable by adjusting end times
                self._fix_timeline_overlaps(state.frames)
                fixed.append(f"Adjusted overlapping frames: {issue.message}")
            else:
                remaining.append(issue.message)

        return fixed, remaining

    def _repair_frame_integrity(
        self,
        state: "PipelineState",
        context: "PipelineContext",
        issues: list["ValidationResult"],
    ) -> tuple[list[str], list[str]]:
        """Repair frame integrity issues."""
        from uuid import uuid4

        fixed: list[str] = []
        remaining: list[str] = []

        for issue in issues:
            if "frame_id" in issue.message.lower():
                # Generate missing frame IDs
                for frame in state.frames:
                    if not frame.get("frame_id"):
                        frame["frame_id"] = str(uuid4())
                fixed.append("Generated missing frame IDs")
            elif "frame_number" in issue.message.lower():
                # Renumber frames
                self._renumber_frames(state.frames)
                fixed.append("Renumbered frames sequentially")
            elif "description" in issue.message.lower():
                # Missing descriptions require regeneration
                remaining.append(f"Missing descriptions require regeneration")
            else:
                remaining.append(issue.message)

        return fixed, remaining

    def _repair_consistency_issues(
        self,
        state: "PipelineState",
        context: "PipelineContext",
        issues: list["ValidationResult"],
    ) -> tuple[list[str], list[str]]:
        """Repair consistency issues."""
        fixed: list[str] = []
        remaining: list[str] = []

        for issue in issues:
            if "scene_number" in issue.message.lower():
                # Scene number issues need sync
                remaining.append("Scene consistency requires sync operation")
            else:
                remaining.append(issue.message)

        return fixed, remaining

    def _apply_auto_fixes(
        self,
        state: "PipelineState",
        context: "PipelineContext",
        result: RepairResult,
    ) -> RepairResult:
        """Apply auto-fixes from validators that support it."""
        from app.services.storyboard.validators import (
            FrameIntegrityValidator,
            TimelineValidator,
        )

        # Timeline auto-fix
        timeline_validator = TimelineValidator()
        if timeline_validator.can_auto_fix():
            timeline_issues = [
                v for v in state.get_failed_validations()
                if v.validator_name == "timeline_validator"
            ]
            if timeline_issues:
                _, fixes = timeline_validator.auto_fix(state, context, timeline_issues)
                result.issues_fixed.extend(fixes)

        # Frame integrity auto-fix
        frame_validator = FrameIntegrityValidator()
        if frame_validator.can_auto_fix():
            frame_issues = [
                v for v in state.get_failed_validations()
                if v.validator_name == "frame_integrity_validator"
            ]
            if frame_issues:
                _, fixes = frame_validator.auto_fix(state, context, frame_issues)
                result.issues_fixed.extend(fixes)

        return result

    def _fix_duration_inconsistencies(self, frames: list[dict[str, Any]]) -> None:
        """Fix duration_seconds to match start_ms/end_ms."""
        for frame in frames:
            start_ms = frame.get("start_ms")
            end_ms = frame.get("end_ms")
            if start_ms is not None and end_ms is not None:
                frame["duration_seconds"] = round((end_ms - start_ms) / 1000.0, 3)

    def _fix_timeline_overlaps(self, frames: list[dict[str, Any]]) -> None:
        """Fix overlapping frames by adjusting end times."""
        timed_frames = [
            f for f in frames
            if f.get("start_ms") is not None and f.get("end_ms") is not None
        ]

        if len(timed_frames) < 2:
            return

        sorted_frames = sorted(timed_frames, key=lambda f: f["start_ms"])

        for i in range(1, len(sorted_frames)):
            prev = sorted_frames[i - 1]
            curr = sorted_frames[i]

            if curr["start_ms"] < prev["end_ms"]:
                # Adjust previous frame's end to current's start
                prev["end_ms"] = curr["start_ms"]
                prev["duration_seconds"] = round(
                    (prev["end_ms"] - prev["start_ms"]) / 1000.0, 3
                )

    def _renumber_frames(self, frames: list[dict[str, Any]]) -> None:
        """Renumber frames sequentially."""
        for i, frame in enumerate(frames, 1):
            frame["frame_number"] = i

    def identify_regeneration_candidates(
        self,
        state: "PipelineState",
        context: "PipelineContext",
    ) -> list[dict[str, Any]]:
        """
        Identify frames/scenes that need regeneration vs repair.

        Returns list of regeneration needs with scene info.
        """
        candidates: list[dict[str, Any]] = []

        # Find scenes with insufficient frames
        frames_by_scene: dict[int, int] = {}
        for frame in state.frames:
            sn = frame.get("scene_number")
            if sn is not None:
                frames_by_scene[sn] = frames_by_scene.get(sn, 0) + 1

        target_frames = state.frames_per_scene
        for sn, count in frames_by_scene.items():
            if count < target_frames:
                candidates.append({
                    "scene_number": sn,
                    "reason": "insufficient_frames",
                    "current_count": count,
                    "target_count": target_frames,
                    "frames_needed": target_frames - count,
                })

        # Find scenes without any frames
        scene_numbers = {s.scene_number for s in context.scenes}
        scenes_with_frames = set(frames_by_scene.keys())
        missing_scenes = scene_numbers - scenes_with_frames

        for sn in missing_scenes:
            candidates.append({
                "scene_number": sn,
                "reason": "no_frames",
                "current_count": 0,
                "target_count": target_frames,
                "frames_needed": target_frames,
            })

        return candidates
