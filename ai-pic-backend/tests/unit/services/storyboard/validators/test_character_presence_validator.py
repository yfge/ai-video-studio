"""Tests for CharacterPresenceValidator."""

import pytest

from app.services.storyboard.pipeline.pipeline_context import (
    PipelineContext,
    SceneContext,
)
from app.services.storyboard.pipeline.pipeline_state import (
    PipelineState,
    ValidationSeverity,
)
from app.services.storyboard.validators.character_presence_validator import (
    CharacterPresenceValidator,
)


@pytest.fixture
def validator():
    """Create CharacterPresenceValidator instance."""
    return CharacterPresenceValidator()


@pytest.fixture
def context_with_characters():
    """Create context with character data."""
    ctx = PipelineContext(script_id=1)
    ctx.scenes = [
        SceneContext(
            scene_number=1,
            scene_id=1,
            dialogues=[
                {"scene_number": 1, "character": "Alice", "content": "Hello"},
                {"scene_number": 1, "character": "Bob", "content": "Hi there"},
            ],
        ),
        SceneContext(
            scene_number=2,
            scene_id=2,
            dialogues=[
                {"scene_number": 2, "character": "Alice", "content": "Goodbye"},
            ],
        ),
    ]
    ctx.character_map = {
        "Alice": {"name": "Alice", "reference_images": ["https://example.com/alice.jpg"]},
        "Bob": {"name": "Bob", "reference_images": ["https://example.com/bob.jpg"]},
    }
    return ctx


@pytest.fixture
def state_with_character_frames():
    """Create state with frames containing character data."""
    state = PipelineState(script_id=1)
    state.frames = [
        {
            "frame_id": "f1",
            "frame_number": 1,
            "scene_number": 1,
            "description": "Alice enters the room",
            "characters": ["Alice"],
        },
        {
            "frame_id": "f2",
            "frame_number": 2,
            "scene_number": 1,
            "description": "Alice and Bob talking",
            "characters": ["Alice", "Bob"],
        },
        {
            "frame_id": "f3",
            "frame_number": 3,
            "scene_number": 2,
            "description": "Alice waves goodbye",
            "characters": ["Alice"],
        },
    ]
    return state


class TestCharacterPresenceValidatorBasics:
    """Test basic validator properties."""

    def test_name(self, validator):
        """Test validator name."""
        assert validator.name == "character_presence_validator"

    def test_can_auto_fix_false(self, validator):
        """Test can_auto_fix returns False (manual review needed)."""
        assert validator.can_auto_fix() is False


class TestNoFramesValidation:
    """Test validation with no frames."""

    def test_no_frames_returns_empty(self, validator, context_with_characters):
        """Test empty results when no frames."""
        state = PipelineState(script_id=1)
        state.frames = []

        results = validator.validate(state, context_with_characters)

        # Should return empty - no frames to validate
        assert len(results) == 0


class TestDialogueCharacterPresence:
    """Test dialogue character presence validation."""

    def test_all_characters_present_pass(
        self, validator, state_with_character_frames, context_with_characters
    ):
        """Test validation passes when all speaking characters appear."""
        results = validator.validate(state_with_character_frames, context_with_characters)
        presence_results = [r for r in results if "speaking" in r.message.lower() or "character" in r.message.lower()]

        assert any(r.passed for r in presence_results)

    def test_missing_character_warning(self, validator, context_with_characters):
        """Test warning when speaking character missing from frames."""
        state = PipelineState(script_id=1)
        state.frames = [
            {
                "frame_id": "f1",
                "scene_number": 1,
                "description": "Alice alone",
                "characters": ["Alice"],  # Bob speaks but not in frame
            },
        ]

        results = validator.validate(state, context_with_characters)
        missing_results = [r for r in results if "missing" in r.message.lower()]

        assert len(missing_results) > 0
        assert missing_results[0].severity == ValidationSeverity.WARNING

    def test_narrator_allowed_missing(self, validator):
        """Test narrator/旁白 can be missing from frames."""
        ctx = PipelineContext(script_id=1)
        ctx.scenes = [
            SceneContext(
                scene_number=1,
                dialogues=[
                    {"scene_number": 1, "character": "旁白", "content": "Narrator speaks"},
                    {"scene_number": 1, "character": "Alice", "content": "Hello"},
                ],
            ),
        ]

        state = PipelineState(script_id=1)
        state.frames = [
            {
                "frame_id": "f1",
                "scene_number": 1,
                "description": "Alice in room",
                "characters": ["Alice"],  # 旁白 not in characters - OK
            },
        ]

        results = validator.validate(state, ctx)
        missing_results = [
            r for r in results
            if "missing" in r.message.lower() and "旁白" in str(r.details)
        ]

        # 旁白 should not be reported as missing
        assert len(missing_results) == 0


class TestReferenceImageValidation:
    """Test reference image availability validation."""

    def test_all_references_available_pass(
        self, validator, state_with_character_frames, context_with_characters
    ):
        """Test validation passes when all characters have references."""
        results = validator.validate(state_with_character_frames, context_with_characters)
        ref_results = [r for r in results if "reference" in r.message.lower()]

        # All characters have references
        assert any(r.passed for r in ref_results)

    def test_missing_references_warning(self, validator):
        """Test warning when character lacks reference images."""
        ctx = PipelineContext(script_id=1)
        ctx.character_map = {
            "Alice": {"name": "Alice", "reference_images": []},  # No images
        }
        ctx.scenes = []

        state = PipelineState(script_id=1)
        state.frames = [
            {
                "frame_id": "f1",
                "scene_number": 1,
                "description": "Alice",
                "characters": ["Alice"],
            },
        ]

        results = validator.validate(state, ctx)
        ref_results = [r for r in results if "reference" in r.message.lower() and "lack" in r.message.lower()]

        assert len(ref_results) > 0
        assert ref_results[0].severity == ValidationSeverity.WARNING


class TestCharacterNameConsistency:
    """Test character name consistency validation."""

    def test_consistent_names_pass(
        self, validator, state_with_character_frames, context_with_characters
    ):
        """Test validation passes with consistent character names."""
        results = validator.validate(state_with_character_frames, context_with_characters)
        consistency_results = [r for r in results if "consistent" in r.message.lower()]

        assert any(r.passed for r in consistency_results)

    def test_similar_names_warning(self, validator):
        """Test warning for potential name variations/typos."""
        ctx = PipelineContext(script_id=1)
        ctx.scenes = []

        state = PipelineState(script_id=1)
        state.frames = [
            {
                "frame_id": "f1",
                "scene_number": 1,
                "description": "Test",
                "characters": ["Alice"],
            },
            {
                "frame_id": "f2",
                "scene_number": 1,
                "description": "Test",
                "characters": ["Alicia"],  # Similar to Alice - potential typo
            },
        ]

        results = validator.validate(state, ctx)
        variation_results = [r for r in results if "variation" in r.message.lower()]

        assert len(variation_results) > 0
        assert variation_results[0].severity == ValidationSeverity.WARNING


class TestCharacterExtractionFromFrames:
    """Test character extraction from different frame formats."""

    def test_characters_as_strings(self, validator, context_with_characters):
        """Test extraction when characters is list of strings."""
        state = PipelineState(script_id=1)
        state.frames = [
            {
                "frame_id": "f1",
                "scene_number": 1,
                "description": "Test",
                "characters": ["Alice", "Bob"],
            },
        ]

        results = validator.validate(state, context_with_characters)

        # Should successfully extract characters
        assert len(results) > 0

    def test_characters_as_dicts(self, validator, context_with_characters):
        """Test extraction when characters is list of dicts."""
        state = PipelineState(script_id=1)
        state.frames = [
            {
                "frame_id": "f1",
                "scene_number": 1,
                "description": "Test",
                "characters": [
                    {"name": "Alice", "role": "protagonist"},
                    {"name": "Bob", "role": "friend"},
                ],
            },
        ]

        results = validator.validate(state, context_with_characters)

        # Should successfully extract character names from dicts
        assert len(results) > 0

    def test_characters_from_description(self, validator):
        """Test character detection from description text."""
        ctx = PipelineContext(script_id=1)
        ctx.scenes = [
            SceneContext(
                scene_number=1,
                dialogues=[
                    {"scene_number": 1, "character": "Alice", "content": "Hello"},
                ],
            ),
        ]

        state = PipelineState(script_id=1)
        state.frames = [
            {
                "frame_id": "f1",
                "scene_number": 1,
                "description": "Alice walks into the room",
                "characters": [],  # Empty but Alice in description
            },
        ]

        results = validator.validate(state, ctx)
        missing_results = [r for r in results if "missing" in r.message.lower()]

        # Alice should be detected from description
        # So no missing character warning
        assert len(missing_results) == 0


class TestSimilarityDetection:
    """Test name similarity detection."""

    def test_similar_short_names(self, validator):
        """Test similar short names are detected."""
        # Direct test of _are_similar
        assert validator._are_similar("John", "Jon") is True
        assert validator._are_similar("Alice", "Alicia") is True

    def test_different_names(self, validator):
        """Test clearly different names are not flagged."""
        assert validator._are_similar("Alice", "Bob") is False
        assert validator._are_similar("John", "Mary") is False

    def test_contained_names(self, validator):
        """Test names where one contains the other."""
        assert validator._are_similar("John", "John Smith") is True
        assert validator._are_similar("Li", "Li Ming") is True

    def test_same_name_not_similar(self, validator):
        """Test same name returns False (not a variation)."""
        assert validator._are_similar("Alice", "Alice") is False
        assert validator._are_similar("Bob", "bob") is False  # Case insensitive
