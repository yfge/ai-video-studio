"""
Timeline continuity validator.

Validates timeline integrity for storyboard frames, ensuring:
- No overlapping time ranges
- Duration consistency
- Proper scene transitions
- Timeline completeness
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.services.storyboard.pipeline.pipeline_state import ValidationResult

if TYPE_CHECKING:
    from app.services.storyboard.pipeline.pipeline_context import PipelineContext
    from app.services.storyboard.pipeline.pipeline_state import PipelineState


class TimelineValidator:
    """
    Validates timeline continuity and consistency for storyboard frames.

    Checks:
    1. No overlapping time ranges between frames
    2. Duration consistency: duration_seconds == (end_ms - start_ms) / 1000
    3. Scene transitions are properly marked
    4. Total duration matches expected (if available)
    """

    DURATION_TOLERANCE_MS = 50  # Allow 50ms tolerance for rounding

    @property
    def name(self) -> str:
        return "timeline_validator"

    @property
    def description(self) -> str:
        return "Validates timeline continuity and duration consistency"

    def validate(
        self,
        state: "PipelineState",
        context: "PipelineContext",
        **kwargs: Any,
    ) -> list[ValidationResult]:
        """Run all timeline validation checks."""
        results: list[ValidationResult] = []

        frames = state.frames
        if not frames:
            results.append(
                ValidationResult.warning(
                    validator_name=self.name,
                    message="No frames to validate timeline",
                )
            )
            return results

        results.extend(self._check_time_overlaps(frames))
        results.extend(self._check_duration_consistency(frames))
        results.extend(self._check_timeline_gaps(frames))
        results.extend(self._check_scene_transitions(frames))
        results.extend(self._check_total_duration(frames, context))

        return results

    def _check_time_overlaps(
        self, frames: list[dict[str, Any]]
    ) -> list[ValidationResult]:
        """Check for overlapping time ranges between frames."""
        results: list[ValidationResult] = []

        # Filter frames with valid time data and sort by start_ms
        timed_frames = [
            f for f in frames
            if f.get("start_ms") is not None and f.get("end_ms") is not None
        ]

        if not timed_frames:
            return results

        sorted_frames = sorted(timed_frames, key=lambda f: f["start_ms"])
        overlaps: list[dict[str, Any]] = []

        for i in range(1, len(sorted_frames)):
            prev = sorted_frames[i - 1]
            curr = sorted_frames[i]

            prev_end = prev["end_ms"]
            curr_start = curr["start_ms"]

            if curr_start < prev_end:
                overlap_ms = prev_end - curr_start
                overlaps.append({
                    "frame_a": prev.get("frame_id") or prev.get("frame_number"),
                    "frame_b": curr.get("frame_id") or curr.get("frame_number"),
                    "frame_a_end_ms": prev_end,
                    "frame_b_start_ms": curr_start,
                    "overlap_ms": overlap_ms,
                })

        if overlaps:
            results.append(
                ValidationResult.error(
                    validator_name=self.name,
                    message=f"Found {len(overlaps)} overlapping time ranges",
                    details={"overlaps": overlaps[:10]},  # Limit detail size
                    suggestions=[
                        "Adjust frame start/end times to eliminate overlaps",
                        "Re-generate storyboard from audio timeline",
                    ],
                )
            )
        else:
            results.append(
                ValidationResult.success(
                    validator_name=self.name,
                    message="No overlapping time ranges found",
                    details={"frames_checked": len(sorted_frames)},
                )
            )

        return results

    def _check_duration_consistency(
        self, frames: list[dict[str, Any]]
    ) -> list[ValidationResult]:
        """Check that duration_seconds matches (end_ms - start_ms) / 1000."""
        results: list[ValidationResult] = []
        inconsistencies: list[dict[str, Any]] = []

        for frame in frames:
            start_ms = frame.get("start_ms")
            end_ms = frame.get("end_ms")
            duration_sec = frame.get("duration_seconds")

            if start_ms is None or end_ms is None:
                continue  # Skip frames without time data

            calculated_duration_ms = end_ms - start_ms
            calculated_duration_sec = calculated_duration_ms / 1000.0

            if duration_sec is not None:
                diff_ms = abs(calculated_duration_ms - duration_sec * 1000)
                if diff_ms > self.DURATION_TOLERANCE_MS:
                    inconsistencies.append({
                        "frame_id": frame.get("frame_id") or frame.get("frame_number"),
                        "start_ms": start_ms,
                        "end_ms": end_ms,
                        "stored_duration_sec": duration_sec,
                        "calculated_duration_sec": round(calculated_duration_sec, 3),
                        "diff_ms": round(diff_ms, 1),
                    })

        if inconsistencies:
            results.append(
                ValidationResult.warning(
                    validator_name=self.name,
                    message=f"{len(inconsistencies)} frames have duration inconsistencies",
                    details={"inconsistencies": inconsistencies[:10]},
                    suggestions=[
                        "Recalculate duration_seconds from start_ms/end_ms",
                        "Use auto_fix to correct durations",
                    ],
                )
            )
        else:
            results.append(
                ValidationResult.success(
                    validator_name=self.name,
                    message="All frame durations are consistent",
                )
            )

        return results

    def _check_timeline_gaps(
        self, frames: list[dict[str, Any]]
    ) -> list[ValidationResult]:
        """Check for gaps in the timeline between frames."""
        results: list[ValidationResult] = []

        timed_frames = [
            f for f in frames
            if f.get("start_ms") is not None and f.get("end_ms") is not None
        ]

        if len(timed_frames) < 2:
            return results

        sorted_frames = sorted(timed_frames, key=lambda f: f["start_ms"])
        gaps: list[dict[str, Any]] = []
        max_allowed_gap_ms = 100  # Small gaps are acceptable

        for i in range(1, len(sorted_frames)):
            prev = sorted_frames[i - 1]
            curr = sorted_frames[i]

            prev_end = prev["end_ms"]
            curr_start = curr["start_ms"]

            gap_ms = curr_start - prev_end
            if gap_ms > max_allowed_gap_ms:
                gaps.append({
                    "after_frame": prev.get("frame_id") or prev.get("frame_number"),
                    "before_frame": curr.get("frame_id") or curr.get("frame_number"),
                    "gap_start_ms": prev_end,
                    "gap_end_ms": curr_start,
                    "gap_ms": gap_ms,
                })

        if gaps:
            total_gap_ms = sum(g["gap_ms"] for g in gaps)
            severity = "warning" if total_gap_ms < 2000 else "error"
            result_method = (
                ValidationResult.warning if severity == "warning"
                else ValidationResult.error
            )
            results.append(
                result_method(
                    validator_name=self.name,
                    message=f"Found {len(gaps)} timeline gaps totaling {total_gap_ms}ms",
                    details={"gaps": gaps[:10], "total_gap_ms": total_gap_ms},
                    suggestions=[
                        "Fill gaps with transition frames",
                        "Extend adjacent frames to cover gaps",
                        "Re-generate from audio timeline",
                    ],
                )
            )
        else:
            results.append(
                ValidationResult.success(
                    validator_name=self.name,
                    message="Timeline is continuous with no significant gaps",
                )
            )

        return results

    def _check_scene_transitions(
        self, frames: list[dict[str, Any]]
    ) -> list[ValidationResult]:
        """Check that scene transitions are properly indicated."""
        results: list[ValidationResult] = []

        timed_frames = [
            f for f in frames if f.get("scene_number") is not None
        ]

        if len(timed_frames) < 2:
            return results

        sorted_frames = sorted(
            timed_frames,
            key=lambda f: (f.get("start_ms") or 0, f.get("frame_number") or 0),
        )

        transitions: list[dict[str, Any]] = []
        for i in range(1, len(sorted_frames)):
            prev = sorted_frames[i - 1]
            curr = sorted_frames[i]

            prev_scene = prev.get("scene_number")
            curr_scene = curr.get("scene_number")

            if prev_scene != curr_scene:
                transitions.append({
                    "from_scene": prev_scene,
                    "to_scene": curr_scene,
                    "at_frame": curr.get("frame_id") or curr.get("frame_number"),
                    "transition_ms": curr.get("start_ms"),
                })

        if transitions:
            results.append(
                ValidationResult.success(
                    validator_name=self.name,
                    message=f"Found {len(transitions)} scene transitions",
                    details={"transitions": transitions},
                )
            )

        return results

    def _check_total_duration(
        self,
        frames: list[dict[str, Any]],
        context: "PipelineContext",
    ) -> list[ValidationResult]:
        """Check if total frame duration matches expected duration."""
        results: list[ValidationResult] = []

        timed_frames = [
            f for f in frames
            if f.get("start_ms") is not None and f.get("end_ms") is not None
        ]

        if not timed_frames:
            return results

        sorted_frames = sorted(timed_frames, key=lambda f: f["start_ms"])
        actual_start = sorted_frames[0]["start_ms"]
        actual_end = sorted_frames[-1]["end_ms"]
        actual_duration_sec = (actual_end - actual_start) / 1000.0

        expected_duration = context.get_total_duration_seconds()

        results.append(
            ValidationResult.success(
                validator_name=self.name,
                message=f"Total timeline duration: {actual_duration_sec:.1f}s",
                details={
                    "start_ms": actual_start,
                    "end_ms": actual_end,
                    "duration_seconds": round(actual_duration_sec, 1),
                    "expected_duration": expected_duration or "unknown",
                    "frame_count": len(timed_frames),
                },
            )
        )

        if expected_duration and expected_duration > 0:
            diff_percent = abs(actual_duration_sec - expected_duration) / expected_duration * 100
            if diff_percent > 20:
                results.append(
                    ValidationResult.warning(
                        validator_name=self.name,
                        message=f"Timeline duration differs from expected by {diff_percent:.0f}%",
                        details={
                            "actual_seconds": round(actual_duration_sec, 1),
                            "expected_seconds": expected_duration,
                            "difference_percent": round(diff_percent, 1),
                        },
                    )
                )

        return results

    def can_auto_fix(self) -> bool:
        """Duration inconsistencies can be auto-fixed."""
        return True

    def auto_fix(
        self,
        state: "PipelineState",
        context: "PipelineContext",
        issues: list[ValidationResult],
    ) -> tuple["PipelineState", list[str]]:
        """Auto-fix duration inconsistencies by recalculating from time data."""
        fixes: list[str] = []

        for frame in state.frames:
            start_ms = frame.get("start_ms")
            end_ms = frame.get("end_ms")

            if start_ms is not None and end_ms is not None:
                calculated_duration = round((end_ms - start_ms) / 1000.0, 3)
                if frame.get("duration_seconds") != calculated_duration:
                    frame["duration_seconds"] = calculated_duration
                    fixes.append(
                        f"Fixed duration for frame {frame.get('frame_id', 'unknown')}"
                    )

        return state, fixes
