"""Tests for StoryboardPipeline."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.storyboard.pipeline.pipeline_context import PipelineContext
from app.services.storyboard.pipeline.pipeline_state import (
    PipelinePhase,
    PipelineState,
    ValidationResult,
)


class TestStoryboardPipelineBasics:
    """Test basic pipeline properties."""

    def test_import_succeeds(self):
        """Test module can be imported."""
        from app.services.storyboard.pipeline.storyboard_pipeline import (
            LANGGRAPH_AVAILABLE,
            StoryboardPipeline,
        )

        assert StoryboardPipeline is not None
        assert isinstance(LANGGRAPH_AVAILABLE, bool)

    def test_pipeline_initialization(self):
        """Test pipeline initializes with components."""
        from app.services.storyboard.pipeline.storyboard_pipeline import (
            StoryboardPipeline,
        )

        mock_db = MagicMock()
        pipeline = StoryboardPipeline(mock_db)

        assert pipeline.db == mock_db
        assert pipeline.precheck is not None
        assert pipeline.retry_strategy is not None
        assert pipeline.repair is not None
        assert len(pipeline.validators) == 4


class TestPipelineNodes:
    """Test individual pipeline nodes."""

    @pytest.fixture
    def pipeline(self):
        """Create pipeline instance."""
        from app.services.storyboard.pipeline.storyboard_pipeline import (
            StoryboardPipeline,
        )

        mock_db = MagicMock()
        return StoryboardPipeline(mock_db)

    @pytest.fixture
    def state_dict(self):
        """Create initial state dict."""
        state = PipelineState(script_id=1)
        ctx = PipelineContext(script_id=1)
        return {
            "pipeline_state": state,
            "context": ctx,
            "script": MagicMock(),
            "episode": None,
        }

    def test_precheck_node(self, pipeline, state_dict):
        """Test precheck node execution."""
        with patch.object(pipeline.precheck, "check_from_context") as mock_check:
            mock_check.return_value = MagicMock(ready=True, errors=[])

            result = pipeline._node_precheck(state_dict)

        assert result["pipeline_state"].phase == PipelinePhase.PRECHECK
        assert "precheck_started" in result["pipeline_state"].reasoning_trace

    def test_precheck_node_failure(self, pipeline, state_dict):
        """Test precheck node when check fails."""
        with patch.object(pipeline.precheck, "check_from_context") as mock_check:
            mock_check.return_value = MagicMock(
                ready=False, message="Missing data", errors=["error1"]
            )

            result = pipeline._node_precheck(state_dict)

        # Should have validation error added
        assert len(result["pipeline_state"].validation_results) > 0

    def test_validate_plan_node(self, pipeline, state_dict):
        """Test plan validation node."""
        result = pipeline._node_validate_plan(state_dict)

        assert result["pipeline_state"].phase == PipelinePhase.VALIDATE_PLAN
        assert "plan_validated" in result["pipeline_state"].reasoning_trace

    def test_validate_frames_node(self, pipeline, state_dict):
        """Test frame validation node."""
        state_dict["pipeline_state"].frames = [
            {"frame_id": "f1", "description": "Test", "scene_number": 1}
        ]

        result = pipeline._node_validate_frames(state_dict)

        assert result["pipeline_state"].phase == PipelinePhase.VALIDATE_FRAMES
        assert "frames_validated" in result["pipeline_state"].reasoning_trace

    def test_validate_timeline_node(self, pipeline, state_dict):
        """Test timeline validation node."""
        state_dict["pipeline_state"].frames = [
            {"frame_id": "f1", "start_ms": 0, "end_ms": 1000, "duration_seconds": 1.0}
        ]

        result = pipeline._node_validate_timeline(state_dict)

        assert result["pipeline_state"].phase == PipelinePhase.VALIDATE_TIMELINE
        assert "timeline_validated" in result["pipeline_state"].reasoning_trace

    def test_recovery_node(self, pipeline, state_dict):
        """Test recovery node."""
        state_dict["pipeline_state"].frames = []
        state_dict["pipeline_state"].add_validation(
            ValidationResult.error("test", "test error")
        )

        result = pipeline._node_recovery(state_dict)

        assert result["pipeline_state"].phase == PipelinePhase.RECOVERY
        assert result["pipeline_state"].recovery_attempts == 1
        # Validation should be cleared for re-validation
        assert len(result["pipeline_state"].validation_results) == 0

    def test_finalize_node_success(self, pipeline, state_dict):
        """Test finalization node on success."""
        state_dict["pipeline_state"].frames = [
            {"frame_id": "f1", "description": "Test"}
        ]
        state_dict["pipeline_state"].has_errors = False

        result = pipeline._node_finalize(state_dict)

        assert result["pipeline_state"].phase == PipelinePhase.COMPLETED
        assert result["pipeline_state"].completed_at is not None

    def test_finalize_node_failure(self, pipeline, state_dict):
        """Test finalization node on failure."""
        state_dict["pipeline_state"].has_errors = True

        result = pipeline._node_finalize(state_dict)

        assert result["pipeline_state"].phase == PipelinePhase.FAILED


class TestFormatResult:
    """Test result formatting."""

    def test_format_success_result(self):
        """Test formatting successful result."""
        from app.services.storyboard.pipeline.storyboard_pipeline import (
            StoryboardPipeline,
        )

        mock_db = MagicMock()
        pipeline = StoryboardPipeline(mock_db)

        state = PipelineState(script_id=1)
        state.frames = [{"frame_id": "f1"}, {"frame_id": "f2"}]
        state.phase = PipelinePhase.COMPLETED
        state.provider_used = "openai"
        state.model_used = "gpt-4"

        state_dict = {"pipeline_state": state}
        result = pipeline._format_result(state_dict)

        assert result["success"] is True
        assert result["frame_count"] == 2
        assert result["phase"] == "completed"
        assert result["provider_used"] == "openai"

    def test_format_error_result(self):
        """Test formatting error result."""
        from app.services.storyboard.pipeline.storyboard_pipeline import (
            StoryboardPipeline,
        )

        mock_db = MagicMock()
        pipeline = StoryboardPipeline(mock_db)

        state = PipelineState(script_id=1)
        state.phase = PipelinePhase.FAILED

        result = pipeline._format_error(state, "Test error message")

        assert result["success"] is False
        assert result["error"] == "Test error message"
        assert result["frames"] == []


@pytest.mark.asyncio
class TestSequentialExecution:
    """Test sequential pipeline execution."""

    async def test_execute_sequential_success(self):
        """Test successful sequential execution."""
        from app.services.storyboard.pipeline.storyboard_pipeline import (
            StoryboardPipeline,
        )

        mock_db = MagicMock()
        pipeline = StoryboardPipeline(mock_db)

        # Mock precheck to pass
        with patch.object(pipeline.precheck, "check_from_context") as mock_check:
            mock_check.return_value = MagicMock(ready=True, errors=[])

            state = PipelineState(script_id=1)
            ctx = PipelineContext(script_id=1)
            mock_script = MagicMock()
            mock_script.id = 1

            result = await pipeline._execute_sequential(state, ctx, mock_script, None)

        assert "success" in result
        assert "frames" in result

    async def test_execute_sequential_precheck_fail(self):
        """Test sequential execution when precheck fails."""
        from app.services.storyboard.pipeline.storyboard_pipeline import (
            StoryboardPipeline,
        )

        mock_db = MagicMock()
        pipeline = StoryboardPipeline(mock_db)

        with patch.object(pipeline.precheck, "check_from_context") as mock_check:
            mock_check.return_value = MagicMock(
                ready=False, message="Missing required data"
            )

            state = PipelineState(script_id=1)
            ctx = PipelineContext(script_id=1)
            mock_script = MagicMock()
            mock_script.id = 1

            result = await pipeline._execute_sequential(state, ctx, mock_script, None)

        assert result["success"] is False
        assert "Missing required data" in result.get("error", "")


class TestPipelineState:
    """Test PipelineState functionality."""

    def test_add_validation(self):
        """Test adding validation results."""
        state = PipelineState(script_id=1)

        state.add_validation(ValidationResult.success("test", "OK"))
        assert len(state.validation_results) == 1
        assert state.has_errors is False

        state.add_validation(ValidationResult.error("test", "Error"))
        assert len(state.validation_results) == 2
        assert state.has_errors is True

    def test_can_recover(self):
        """Test recovery check."""
        state = PipelineState(script_id=1, max_recovery_attempts=2)

        assert state.can_recover() is True

        state.recovery_attempts = 1
        assert state.can_recover() is True

        state.recovery_attempts = 2
        assert state.can_recover() is False

    def test_record_recovery(self):
        """Test recovery recording."""
        state = PipelineState(script_id=1)

        state.record_recovery("test_action", {"key": "value"})

        assert state.recovery_attempts == 1
        assert len(state.recovery_history) == 1
        assert state.recovery_history[0]["action"] == "test_action"

    def test_get_failed_validations(self):
        """Test getting failed validations."""
        state = PipelineState(script_id=1)
        state.add_validation(ValidationResult.success("v1", "OK"))
        state.add_validation(ValidationResult.error("v2", "Error"))
        state.add_validation(ValidationResult.warning("v3", "Warning"))

        failed = state.get_failed_validations()

        assert len(failed) == 1
        assert failed[0].validator_name == "v2"

    def test_to_dict(self):
        """Test state serialization."""
        state = PipelineState(script_id=1, episode_id=2)
        state.frames = [{"frame_id": "f1"}]
        state.provider_used = "test_provider"

        d = state.to_dict()

        assert d["script_id"] == 1
        assert d["episode_id"] == 2
        assert d["frames_count"] == 1
        assert d["provider_used"] == "test_provider"
