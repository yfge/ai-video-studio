"""Tests for FrameIntegrityValidator."""

import pytest

from app.services.storyboard.pipeline.pipeline_context import PipelineContext
from app.services.storyboard.pipeline.pipeline_state import (
    PipelineState,
    ValidationSeverity,
)
from app.services.storyboard.validators.frame_integrity_validator import (
    FrameIntegrityValidator,
)


@pytest.fixture
def validator():
    """Create FrameIntegrityValidator instance."""
    return FrameIntegrityValidator()


@pytest.fixture
def empty_context():
    """Create empty pipeline context."""
    return PipelineContext(script_id=1)


@pytest.fixture
def state_with_valid_frames():
    """Create state with valid frames."""
    state = PipelineState(script_id=1)
    state.frames = [
        {
            "frame_id": "f1",
            "frame_number": 1,
            "scene_number": 1,
            "description": "A person walks into a room",
            "duration_seconds": 2.0,
            "image_url": "https://example.com/image1.jpg",
        },
        {
            "frame_id": "f2",
            "frame_number": 2,
            "scene_number": 1,
            "description": "They look around nervously",
            "duration_seconds": 1.5,
        },
        {
            "frame_id": "f3",
            "frame_number": 3,
            "scene_number": 2,
            "description": "Cut to exterior shot",
            "duration_seconds": 3.0,
        },
    ]
    return state


class TestFrameIntegrityValidatorBasics:
    """Test basic validator properties."""

    def test_name(self, validator):
        """Test validator name."""
        assert validator.name == "frame_integrity_validator"

    def test_can_auto_fix(self, validator):
        """Test can_auto_fix returns True."""
        assert validator.can_auto_fix() is True


class TestNoFramesValidation:
    """Test validation with no frames."""

    def test_no_frames_error(self, validator, empty_context):
        """Test error when no frames to validate."""
        state = PipelineState(script_id=1)
        state.frames = []

        results = validator.validate(state, empty_context)

        assert len(results) == 1
        assert results[0].passed is False
        assert "no frames" in results[0].message.lower()


class TestRequiredFieldsValidation:
    """Test required fields validation."""

    def test_all_required_fields_pass(self, validator, state_with_valid_frames, empty_context):
        """Test validation passes when all required fields present."""
        results = validator.validate(state_with_valid_frames, empty_context)
        required_results = [r for r in results if "required" in r.message.lower()]

        assert any(r.passed for r in required_results)

    def test_missing_frame_id_error(self, validator, empty_context):
        """Test missing frame_id generates error."""
        state = PipelineState(script_id=1)
        state.frames = [
            {"frame_number": 1, "description": "Test"},  # Missing frame_id
        ]

        results = validator.validate(state, empty_context)
        required_results = [r for r in results if "frame_id" in r.message.lower()]

        assert len(required_results) > 0
        assert required_results[0].passed is False

    def test_missing_description_error(self, validator, empty_context):
        """Test missing description generates error."""
        state = PipelineState(script_id=1)
        state.frames = [
            {"frame_id": "f1", "frame_number": 1},  # Missing description
        ]

        results = validator.validate(state, empty_context)
        required_results = [r for r in results if "description" in r.message.lower()]

        assert len(required_results) > 0
        assert required_results[0].passed is False

    def test_empty_description_error(self, validator, empty_context):
        """Test empty description generates error."""
        state = PipelineState(script_id=1)
        state.frames = [
            {"frame_id": "f1", "frame_number": 1, "description": "   "},  # Empty/whitespace
        ]

        results = validator.validate(state, empty_context)
        required_results = [r for r in results if "description" in r.message.lower()]

        assert len(required_results) > 0
        assert required_results[0].passed is False


class TestUrlValidation:
    """Test URL field validation."""

    def test_valid_urls_pass(self, validator, state_with_valid_frames, empty_context):
        """Test valid URLs pass validation."""
        results = validator.validate(state_with_valid_frames, empty_context)
        url_results = [r for r in results if "url" in r.message.lower()]

        # Valid URLs should pass
        assert all(r.passed for r in url_results if r.severity != ValidationSeverity.INFO)

    def test_invalid_url_warning(self, validator, empty_context):
        """Test invalid URL generates warning."""
        state = PipelineState(script_id=1)
        state.frames = [
            {
                "frame_id": "f1",
                "description": "Test",
                "image_url": "not-a-valid-url",
            },
        ]

        results = validator.validate(state, empty_context)
        url_results = [r for r in results if "url" in r.message.lower() and "invalid" in r.message.lower()]

        assert len(url_results) > 0
        assert url_results[0].severity == ValidationSeverity.WARNING

    def test_data_url_valid(self, validator, empty_context):
        """Test data URLs are considered valid."""
        state = PipelineState(script_id=1)
        state.frames = [
            {
                "frame_id": "f1",
                "description": "Test",
                "image_url": "data:image/png;base64,abc123",
            },
        ]

        results = validator.validate(state, empty_context)
        url_results = [r for r in results if "invalid" in r.message.lower() and "url" in r.message.lower()]

        # Data URL should be valid
        assert len(url_results) == 0


class TestFrameNumberingValidation:
    """Test frame numbering validation."""

    def test_sequential_numbering_passes(self, validator, state_with_valid_frames, empty_context):
        """Test sequential numbering passes."""
        results = validator.validate(state_with_valid_frames, empty_context)
        numbering_results = [r for r in results if "numbering" in r.message.lower() or "sequential" in r.message.lower()]

        assert any(r.passed for r in numbering_results)

    def test_duplicate_frame_id_error(self, validator, empty_context):
        """Test duplicate frame_id generates error."""
        state = PipelineState(script_id=1)
        state.frames = [
            {"frame_id": "f1", "frame_number": 1, "description": "Test 1"},
            {"frame_id": "f1", "frame_number": 2, "description": "Test 2"},  # Duplicate ID
        ]

        results = validator.validate(state, empty_context)
        duplicate_results = [r for r in results if "duplicate" in r.message.lower()]

        assert len(duplicate_results) > 0
        assert duplicate_results[0].passed is False

    def test_non_sequential_numbering_warning(self, validator, empty_context):
        """Test non-sequential numbering generates warning."""
        state = PipelineState(script_id=1)
        state.frames = [
            {"frame_id": "f1", "frame_number": 1, "description": "Test 1"},
            {"frame_id": "f2", "frame_number": 3, "description": "Test 2"},  # Gap
            {"frame_id": "f3", "frame_number": 4, "description": "Test 3"},
        ]

        results = validator.validate(state, empty_context)
        numbering_results = [r for r in results if "sequential" in r.message.lower() or "numbering" in r.message.lower()]

        # Should have warning about non-sequential
        assert any(r.severity == ValidationSeverity.WARNING for r in numbering_results)


class TestFramesPerSceneValidation:
    """Test minimum frames per scene validation."""

    def test_sufficient_frames_pass(self, validator, state_with_valid_frames, empty_context):
        """Test sufficient frames per scene passes."""
        results = validator.validate(
            state_with_valid_frames, empty_context, min_frames_per_scene=1
        )
        scene_results = [r for r in results if "scene" in r.message.lower() and "frame" in r.message.lower()]

        assert any(r.passed for r in scene_results)

    def test_insufficient_frames_warning(self, validator, empty_context):
        """Test insufficient frames per scene generates warning."""
        state = PipelineState(script_id=1)
        state.frames = [
            {"frame_id": "f1", "frame_number": 1, "scene_number": 1, "description": "Test"},
        ]

        results = validator.validate(state, empty_context, min_frames_per_scene=3)
        insufficient_results = [r for r in results if "fewer" in r.message.lower() or "insufficient" in r.message.lower()]

        assert len(insufficient_results) > 0
        assert insufficient_results[0].severity == ValidationSeverity.WARNING


class TestAutoFix:
    """Test auto-fix functionality."""

    def test_auto_fix_generates_frame_ids(self, validator, empty_context):
        """Test auto_fix generates missing frame IDs."""
        state = PipelineState(script_id=1)
        state.frames = [
            {"description": "Test 1"},  # Missing frame_id
            {"frame_id": "f2", "description": "Test 2"},
        ]

        issues = validator.validate(state, empty_context)
        new_state, fixes = validator.auto_fix(state, empty_context, issues)

        # First frame should now have a frame_id
        assert new_state.frames[0].get("frame_id") is not None
        assert len(new_state.frames[0]["frame_id"]) > 0

    def test_auto_fix_renumbers_frames(self, validator, empty_context):
        """Test auto_fix renumbers frames sequentially."""
        state = PipelineState(script_id=1)
        state.frames = [
            {"frame_id": "f1", "frame_number": 5, "description": "Test 1"},
            {"frame_id": "f2", "frame_number": 10, "description": "Test 2"},
        ]

        issues = validator.validate(state, empty_context)
        new_state, fixes = validator.auto_fix(state, empty_context, issues)

        # Frames should be renumbered 1, 2
        assert new_state.frames[0]["frame_number"] == 1
        assert new_state.frames[1]["frame_number"] == 2
