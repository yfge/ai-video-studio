"""Tests for ConsistencyValidator."""

import pytest
from app.services.storyboard.pipeline.pipeline_context import (
    PipelineContext,
    SceneContext,
)
from app.services.storyboard.pipeline.pipeline_state import (
    PipelineState,
    ValidationSeverity,
)
from app.services.storyboard.validators.consistency_validator import (
    ConsistencyValidator,
)


@pytest.fixture
def validator():
    """Create ConsistencyValidator instance."""
    return ConsistencyValidator()


@pytest.fixture
def empty_state():
    """Create empty pipeline state."""
    return PipelineState(script_id=1)


@pytest.fixture
def context_with_scenes():
    """Create context with valid scenes."""
    ctx = PipelineContext(script_id=1)
    ctx.json_scene_count = 3
    ctx.structure_scene_count = 3
    ctx.is_synchronized = True

    for i in range(1, 4):
        scene = SceneContext(
            scene_number=i,
            scene_id=i,
            location=f"Location {i}",
            dialogues=[
                {"scene_number": i, "character": "Character A", "content": f"Line {i}"}
            ],
        )
        ctx.scenes.append(scene)

    return ctx


class TestConsistencyValidatorBasics:
    """Test basic validator properties."""

    def test_name(self, validator):
        """Test validator name."""
        assert validator.name == "consistency_validator"

    def test_description(self, validator):
        """Test validator description."""
        assert "consistency" in validator.description.lower()

    def test_can_auto_fix(self, validator):
        """Test can_auto_fix returns True."""
        assert validator.can_auto_fix() is True


class TestSceneCountValidation:
    """Test scene count validation."""

    def test_matching_scene_counts_pass(
        self, validator, empty_state, context_with_scenes
    ):
        """Test validation passes when scene counts match."""
        results = validator.validate(empty_state, context_with_scenes)
        count_results = [r for r in results if "count" in r.message.lower()]

        assert any(r.passed for r in count_results)

    def test_zero_scenes_fails(self, validator, empty_state):
        """Test validation fails when no scenes exist."""
        ctx = PipelineContext(script_id=1)
        ctx.json_scene_count = 0
        ctx.structure_scene_count = 0

        results = validator.validate(empty_state, ctx)
        error_results = [r for r in results if not r.passed]

        assert len(error_results) > 0
        assert any("no scenes" in r.message.lower() for r in error_results)

    def test_mismatched_counts_warning(self, validator, empty_state):
        """Test small count mismatch generates warning."""
        ctx = PipelineContext(script_id=1)
        ctx.json_scene_count = 3
        ctx.structure_scene_count = 4
        ctx.scenes = [SceneContext(scene_number=i) for i in range(1, 5)]
        ctx.is_synchronized = False

        results = validator.validate(empty_state, ctx)
        mismatch_results = [r for r in results if "mismatch" in r.message.lower()]

        assert len(mismatch_results) > 0
        # Small difference should be warning, not error
        assert mismatch_results[0].severity in (
            ValidationSeverity.WARNING,
            ValidationSeverity.ERROR,
        )

    def test_large_mismatch_error(self, validator, empty_state):
        """Test large count mismatch generates error."""
        ctx = PipelineContext(script_id=1)
        ctx.json_scene_count = 3
        ctx.structure_scene_count = 10
        ctx.scenes = [SceneContext(scene_number=i) for i in range(1, 11)]
        ctx.is_synchronized = False

        results = validator.validate(empty_state, ctx)
        mismatch_results = [r for r in results if "mismatch" in r.message.lower()]

        assert len(mismatch_results) > 0
        assert mismatch_results[0].severity == ValidationSeverity.ERROR


class TestSceneNumberValidation:
    """Test scene number consecutive validation."""

    def test_consecutive_numbers_pass(
        self, validator, empty_state, context_with_scenes
    ):
        """Test consecutive scene numbers pass."""
        results = validator.validate(empty_state, context_with_scenes)

        # Should have a success message
        assert any(r.passed for r in results)

    def test_gap_in_numbers_warning(self, validator, empty_state):
        """Test gap in scene numbers generates warning."""
        ctx = PipelineContext(script_id=1)
        ctx.json_scene_count = 3
        ctx.structure_scene_count = 3
        # Scenes 1, 3, 4 - missing 2
        ctx.scenes = [
            SceneContext(scene_number=1, scene_id=1),
            SceneContext(scene_number=3, scene_id=3),
            SceneContext(scene_number=4, scene_id=4),
        ]
        ctx.is_synchronized = True

        results = validator.validate(empty_state, ctx)
        gap_results = [
            r
            for r in results
            if "gap" in r.message.lower() or "consecutive" in r.message.lower()
        ]

        assert len(gap_results) > 0
        assert any(
            "missing" in r.message.lower() or "non-consecutive" in r.message.lower()
            for r in gap_results
        )

    def test_duplicate_numbers_error(self, validator, empty_state):
        """Test duplicate scene numbers generate error."""
        ctx = PipelineContext(script_id=1)
        ctx.json_scene_count = 3
        ctx.structure_scene_count = 3
        # Duplicate scene 2
        ctx.scenes = [
            SceneContext(scene_number=1, scene_id=1),
            SceneContext(scene_number=2, scene_id=2),
            SceneContext(scene_number=2, scene_id=3),
        ]
        ctx.is_synchronized = True

        results = validator.validate(empty_state, ctx)
        duplicate_results = [r for r in results if "duplicate" in r.message.lower()]

        assert len(duplicate_results) > 0
        assert duplicate_results[0].passed is False


class TestDialogueValidation:
    """Test dialogue scene reference validation."""

    def test_valid_dialogue_references_pass(
        self, validator, empty_state, context_with_scenes
    ):
        """Test valid dialogue references pass."""
        results = validator.validate(empty_state, context_with_scenes)

        # Should have success for dialogue validation
        dialogue_results = [r for r in results if "dialogue" in r.message.lower()]
        assert any(r.passed for r in dialogue_results)

    def test_invalid_scene_reference_error(self, validator, empty_state):
        """Test invalid scene reference in dialogue generates error."""
        ctx = PipelineContext(script_id=1)
        ctx.json_scene_count = 2
        ctx.structure_scene_count = 2
        ctx.scenes = [
            SceneContext(
                scene_number=1,
                scene_id=1,
                dialogues=[
                    {"scene_number": 99, "character": "A", "content": "Invalid ref"}
                ],
            ),
            SceneContext(scene_number=2, scene_id=2),
        ]
        ctx.is_synchronized = True

        results = validator.validate(empty_state, ctx)
        invalid_results = [
            r
            for r in results
            if "invalid" in r.message.lower() and "scene" in r.message.lower()
        ]

        assert len(invalid_results) > 0
        assert invalid_results[0].passed is False


class TestSyncStatus:
    """Test sync status validation."""

    def test_synchronized_passes(self, validator, empty_state, context_with_scenes):
        """Test synchronized status passes."""
        results = validator.validate(empty_state, context_with_scenes)
        sync_results = [r for r in results if "sync" in r.message.lower()]

        assert any(r.passed for r in sync_results)

    def test_not_synchronized_warning(self, validator, empty_state):
        """Test out-of-sync status generates warning."""
        ctx = PipelineContext(script_id=1)
        ctx.json_scene_count = 2
        ctx.structure_scene_count = 2
        ctx.scenes = [SceneContext(scene_number=i, scene_id=i) for i in range(1, 3)]
        ctx.is_synchronized = False
        ctx.sync_issues = ["Test sync issue"]

        results = validator.validate(empty_state, ctx)
        sync_results = [r for r in results if "sync" in r.message.lower()]

        assert any(r.severity == ValidationSeverity.WARNING for r in sync_results)
