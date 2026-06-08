"""Tests for TimelineValidator."""

import pytest
from app.services.storyboard.pipeline.pipeline_context import PipelineContext
from app.services.storyboard.pipeline.pipeline_state import (
    PipelineState,
    ValidationSeverity,
)
from app.services.storyboard.validators.timeline_validator import TimelineValidator


@pytest.fixture
def validator():
    """Create TimelineValidator instance."""
    return TimelineValidator()


@pytest.fixture
def empty_context():
    """Create empty pipeline context."""
    return PipelineContext(script_id=1)


@pytest.fixture
def state_with_frames():
    """Create state with valid frames."""
    state = PipelineState(script_id=1)
    state.frames = [
        {
            "frame_id": "f1",
            "frame_number": 1,
            "scene_number": 1,
            "start_ms": 0,
            "end_ms": 2000,
            "duration_seconds": 2.0,
            "description": "Frame 1",
        },
        {
            "frame_id": "f2",
            "frame_number": 2,
            "scene_number": 1,
            "start_ms": 2000,
            "end_ms": 4000,
            "duration_seconds": 2.0,
            "description": "Frame 2",
        },
        {
            "frame_id": "f3",
            "frame_number": 3,
            "scene_number": 2,
            "start_ms": 4000,
            "end_ms": 6000,
            "duration_seconds": 2.0,
            "description": "Frame 3",
        },
    ]
    return state


class TestTimelineValidatorBasics:
    """Test basic validator properties."""

    def test_name(self, validator):
        """Test validator name."""
        assert validator.name == "timeline_validator"

    def test_can_auto_fix(self, validator):
        """Test can_auto_fix returns True."""
        assert validator.can_auto_fix() is True


class TestNoFramesValidation:
    """Test validation with no frames."""

    def test_no_frames_warning(self, validator, empty_context):
        """Test warning when no frames to validate."""
        state = PipelineState(script_id=1)
        state.frames = []

        results = validator.validate(state, empty_context)

        assert len(results) == 1
        assert results[0].severity == ValidationSeverity.WARNING
        assert "no frames" in results[0].message.lower()


class TestTimeOverlapValidation:
    """Test time overlap detection."""

    def test_no_overlaps_passes(self, validator, state_with_frames, empty_context):
        """Test validation passes with no overlaps."""
        results = validator.validate(state_with_frames, empty_context)
        overlap_results = [r for r in results if "overlap" in r.message.lower()]

        assert any(r.passed for r in overlap_results)

    def test_overlap_detected_error(self, validator, empty_context):
        """Test overlap detection generates error."""
        state = PipelineState(script_id=1)
        state.frames = [
            {"frame_id": "f1", "start_ms": 0, "end_ms": 3000},
            {"frame_id": "f2", "start_ms": 2000, "end_ms": 5000},  # Overlaps with f1
        ]

        results = validator.validate(state, empty_context)
        overlap_results = [r for r in results if "overlap" in r.message.lower()]

        assert len(overlap_results) > 0
        assert overlap_results[0].passed is False
        assert overlap_results[0].severity == ValidationSeverity.ERROR

    def test_overlap_details_included(self, validator, empty_context):
        """Test overlap details are included in result."""
        state = PipelineState(script_id=1)
        state.frames = [
            {"frame_id": "f1", "start_ms": 0, "end_ms": 3000},
            {"frame_id": "f2", "start_ms": 2000, "end_ms": 5000},
        ]

        results = validator.validate(state, empty_context)
        overlap_results = [r for r in results if "overlap" in r.message.lower()]

        assert overlap_results[0].details.get("overlaps")


class TestDurationConsistency:
    """Test duration consistency validation."""

    def test_consistent_durations_pass(
        self, validator, state_with_frames, empty_context
    ):
        """Test consistent durations pass."""
        results = validator.validate(state_with_frames, empty_context)
        duration_results = [r for r in results if "duration" in r.message.lower()]

        assert any(r.passed for r in duration_results)

    def test_inconsistent_duration_warning(self, validator, empty_context):
        """Test inconsistent duration generates warning."""
        state = PipelineState(script_id=1)
        state.frames = [
            {
                "frame_id": "f1",
                "start_ms": 0,
                "end_ms": 2000,
                "duration_seconds": 3.0,  # Should be 2.0
            },
        ]

        results = validator.validate(state, empty_context)
        duration_results = [r for r in results if "inconsisten" in r.message.lower()]

        assert len(duration_results) > 0
        assert duration_results[0].severity == ValidationSeverity.WARNING

    def test_tolerance_respected(self, validator, empty_context):
        """Test small duration differences within tolerance pass."""
        state = PipelineState(script_id=1)
        state.frames = [
            {
                "frame_id": "f1",
                "start_ms": 0,
                "end_ms": 2000,
                "duration_seconds": 2.01,  # Within 50ms tolerance
            },
        ]

        results = validator.validate(state, empty_context)

        # Should pass due to tolerance
        assert all(r.passed for r in results)


class TestTimelineGaps:
    """Test timeline gap detection."""

    def test_no_gaps_passes(self, validator, state_with_frames, empty_context):
        """Test no gaps passes validation."""
        results = validator.validate(state_with_frames, empty_context)
        gap_results = [
            r
            for r in results
            if "gap" in r.message.lower() or "continuous" in r.message.lower()
        ]

        assert any(r.passed for r in gap_results)

    def test_gap_detected_warning(self, validator, empty_context):
        """Test gap detection generates warning."""
        state = PipelineState(script_id=1)
        state.frames = [
            {"frame_id": "f1", "start_ms": 0, "end_ms": 1000},
            {"frame_id": "f2", "start_ms": 2000, "end_ms": 3000},  # 1000ms gap
        ]

        results = validator.validate(state, empty_context)
        gap_results = [r for r in results if "gap" in r.message.lower()]

        assert len(gap_results) > 0
        # Small gap should be warning
        assert gap_results[0].severity in (
            ValidationSeverity.WARNING,
            ValidationSeverity.ERROR,
        )

    def test_small_gap_ignored(self, validator, empty_context):
        """Test very small gaps are ignored."""
        state = PipelineState(script_id=1)
        state.frames = [
            {"frame_id": "f1", "start_ms": 0, "end_ms": 1000},
            {"frame_id": "f2", "start_ms": 1050, "end_ms": 2000},  # 50ms gap
        ]

        results = validator.validate(state, empty_context)
        gap_results = [
            r for r in results if "gap" in r.message.lower() and not r.passed
        ]

        # Small gaps under threshold should not be reported as failures
        assert len(gap_results) == 0


class TestSceneTransitions:
    """Test scene transition detection."""

    def test_transitions_detected(self, validator, state_with_frames, empty_context):
        """Test scene transitions are detected."""
        results = validator.validate(state_with_frames, empty_context)
        transition_results = [r for r in results if "transition" in r.message.lower()]

        assert len(transition_results) > 0
        # Scene 1 -> Scene 2 transition
        assert transition_results[0].details.get("transitions")


class TestAutoFix:
    """Test auto-fix functionality."""

    def test_auto_fix_corrects_durations(self, validator, empty_context):
        """Test auto_fix corrects duration inconsistencies."""
        state = PipelineState(script_id=1)
        state.frames = [
            {"frame_id": "f1", "start_ms": 0, "end_ms": 2000, "duration_seconds": 5.0},
            {
                "frame_id": "f2",
                "start_ms": 2000,
                "end_ms": 4000,
                "duration_seconds": 1.0,
            },
        ]

        issues = validator.validate(state, empty_context)
        new_state, fixes = validator.auto_fix(state, empty_context, issues)

        # Check durations were corrected
        assert new_state.frames[0]["duration_seconds"] == 2.0
        assert new_state.frames[1]["duration_seconds"] == 2.0
        assert len(fixes) > 0

    def test_auto_fix_with_no_time_data(self, validator, empty_context):
        """Test auto_fix handles frames without time data."""
        state = PipelineState(script_id=1)
        state.frames = [
            {"frame_id": "f1", "duration_seconds": 2.0},  # No start_ms/end_ms
        ]

        issues = []
        new_state, fixes = validator.auto_fix(state, empty_context, issues)

        # Should not crash, duration unchanged
        assert new_state.frames[0]["duration_seconds"] == 2.0
