"""Unit tests for VisualContinuityValidator."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from app.services.storyboard.pipeline.pipeline_state import (
    PipelineState,
    ValidationSeverity,
)
from app.services.storyboard.validators.visual_continuity_validator import (
    VisualContinuityValidator,
)


@pytest.fixture
def validator() -> VisualContinuityValidator:
    """Create a validator instance."""
    return VisualContinuityValidator()


@pytest.fixture
def mock_context() -> MagicMock:
    """Create a mock pipeline context."""
    context = MagicMock()
    context.scenes = []
    return context


@pytest.fixture
def base_state() -> PipelineState:
    """Create a base pipeline state."""
    return PipelineState(script_id=1, episode_id=1)


class TestVisualContinuityValidator:
    """Tests for VisualContinuityValidator."""

    def test_validator_name(self, validator: VisualContinuityValidator) -> None:
        """Test validator name property."""
        assert validator.name == "visual_continuity_validator"

    def test_validator_description(self, validator: VisualContinuityValidator) -> None:
        """Test validator description property."""
        assert "visual continuity" in validator.description.lower()

    def test_validate_empty_frames(
        self,
        validator: VisualContinuityValidator,
        base_state: PipelineState,
        mock_context: MagicMock,
    ) -> None:
        """Test validation with empty frames."""
        base_state.frames = []
        results = validator.validate(base_state, mock_context)
        assert len(results) == 1
        assert results[0].passed is True
        assert "insufficient" in results[0].message.lower()

    def test_validate_single_frame(
        self,
        validator: VisualContinuityValidator,
        base_state: PipelineState,
        mock_context: MagicMock,
    ) -> None:
        """Test validation with single frame."""
        base_state.frames = [{"frame_number": 1, "description": "A scene"}]
        results = validator.validate(base_state, mock_context)
        assert len(results) == 1
        assert results[0].passed is True

    # ============================================
    # Costume Continuity Tests
    # ============================================

    def test_costume_consistency_pass(
        self,
        validator: VisualContinuityValidator,
        base_state: PipelineState,
        mock_context: MagicMock,
    ) -> None:
        """Test costume consistency with matching outfits."""
        base_state.frames = [
            {
                "frame_number": 1,
                "characters": [{"name": "Alice"}],
                "visual_description": "Alice穿着红色裙子站在门口",
            },
            {
                "frame_number": 2,
                "characters": [{"name": "Alice"}],
                "visual_description": "Alice穿着红色裙子走进房间",
            },
        ]
        results = validator.validate(base_state, mock_context)

        costume_warnings = [
            r
            for r in results
            if "costume" in r.message.lower()
            and r.severity == ValidationSeverity.WARNING
        ]
        assert len(costume_warnings) == 0

    def test_costume_inconsistency_detected(
        self,
        validator: VisualContinuityValidator,
        base_state: PipelineState,
        mock_context: MagicMock,
    ) -> None:
        """Test detection of costume inconsistency."""
        base_state.frames = [
            {
                "frame_number": 1,
                "characters": [{"name": "Alice"}],
                "visual_description": "Alice穿着红色裙子",
            },
            {
                "frame_number": 2,
                "characters": [{"name": "Alice"}],
                "visual_description": "Alice穿着西装",
            },
        ]
        results = validator.validate(base_state, mock_context)

        costume_warnings = [
            r
            for r in results
            if "costume" in r.message.lower()
            and r.severity == ValidationSeverity.WARNING
        ]
        assert len(costume_warnings) > 0

    # ============================================
    # Hairstyle Continuity Tests
    # ============================================

    def test_hairstyle_consistency_pass(
        self,
        validator: VisualContinuityValidator,
        base_state: PipelineState,
        mock_context: MagicMock,
    ) -> None:
        """Test hairstyle consistency with matching hair."""
        base_state.frames = [
            {
                "frame_number": 1,
                "characters": [{"name": "Bob"}],
                "visual_description": "Bob有着短发，站在窗边",
            },
            {
                "frame_number": 2,
                "characters": [{"name": "Bob"}],
                "visual_description": "Bob短发，坐在椅子上",
            },
        ]
        results = validator.validate(base_state, mock_context)

        hair_warnings = [
            r
            for r in results
            if "hairstyle" in r.message.lower()
            and r.severity == ValidationSeverity.WARNING
        ]
        assert len(hair_warnings) == 0

    def test_hairstyle_inconsistency_detected(
        self,
        validator: VisualContinuityValidator,
        base_state: PipelineState,
        mock_context: MagicMock,
    ) -> None:
        """Test detection of hairstyle inconsistency."""
        base_state.frames = [
            {
                "frame_number": 1,
                "characters": [{"name": "Carol"}],
                "visual_description": "Carol长发飘飘",
            },
            {
                "frame_number": 2,
                "characters": [{"name": "Carol"}],
                "visual_description": "Carol短发利落",
            },
        ]
        results = validator.validate(base_state, mock_context)

        hair_warnings = [
            r
            for r in results
            if "hair" in r.message.lower() and r.severity == ValidationSeverity.WARNING
        ]
        assert len(hair_warnings) > 0

    # ============================================
    # Props Continuity Tests
    # ============================================

    def test_props_continuity_pass(
        self,
        validator: VisualContinuityValidator,
        base_state: PipelineState,
        mock_context: MagicMock,
    ) -> None:
        """Test props consistency."""
        base_state.frames = [
            {
                "frame_number": 1,
                "characters": [{"name": "Dan"}],
                "visual_description": "Dan手持手机走来",
            },
            {
                "frame_number": 2,
                "characters": [{"name": "Dan"}],
                "visual_description": "Dan看着手中的手机",
            },
        ]
        results = validator.validate(base_state, mock_context)

        prop_warnings = [
            r
            for r in results
            if "prop" in r.message.lower() and r.severity == ValidationSeverity.WARNING
        ]
        assert len(prop_warnings) == 0

    def test_props_disappearing_detected(
        self,
        validator: VisualContinuityValidator,
        base_state: PipelineState,
        mock_context: MagicMock,
    ) -> None:
        """Test detection of disappearing props."""
        base_state.frames = [
            {
                "frame_number": 1,
                "characters": [{"name": "Eve"}],
                "visual_description": "Eve站着",
            },
            {
                "frame_number": 2,
                "characters": [{"name": "Eve"}],
                "visual_description": "Eve手持眼镜看书",
            },
            {
                "frame_number": 3,
                "characters": [{"name": "Eve"}],
                "visual_description": "Eve站着思考",
            },
        ]
        results = validator.validate(base_state, mock_context)

        prop_warnings = [
            r
            for r in results
            if "prop" in r.message.lower() and r.severity == ValidationSeverity.WARNING
        ]
        assert len(prop_warnings) > 0

    # ============================================
    # Movement Feasibility Tests
    # ============================================

    def test_movement_feasibility_pass(
        self,
        validator: VisualContinuityValidator,
        base_state: PipelineState,
        mock_context: MagicMock,
    ) -> None:
        """Test feasible movement."""
        base_state.frames = [
            {
                "frame_number": 1,
                "characters": [{"name": "Frank"}],
                "visual_description": "Frank站在画面左侧",
            },
            {
                "frame_number": 2,
                "characters": [{"name": "Frank"}],
                "visual_description": "Frank走到中央位置",
            },
        ]
        results = validator.validate(base_state, mock_context)

        teleport_warnings = [
            r
            for r in results
            if "teleport" in r.message.lower()
            and r.severity == ValidationSeverity.WARNING
        ]
        assert len(teleport_warnings) == 0

    def test_teleportation_detected(
        self,
        validator: VisualContinuityValidator,
        base_state: PipelineState,
        mock_context: MagicMock,
    ) -> None:
        """Test detection of character teleportation."""
        base_state.frames = [
            {
                "frame_number": 1,
                "characters": [{"name": "Grace"}],
                "visual_description": "Grace站在画面左侧",
            },
            {
                "frame_number": 2,
                "characters": [{"name": "Grace"}],
                "visual_description": "Grace出现在画面右侧",
            },
        ]
        results = validator.validate(base_state, mock_context)

        teleport_warnings = [
            r
            for r in results
            if "teleport" in r.message.lower()
            and r.severity == ValidationSeverity.WARNING
        ]
        assert len(teleport_warnings) > 0

    # ============================================
    # Pose Transition Tests
    # ============================================

    def test_valid_pose_transition(
        self,
        validator: VisualContinuityValidator,
        base_state: PipelineState,
        mock_context: MagicMock,
    ) -> None:
        """Test valid pose transition."""
        base_state.frames = [
            {
                "frame_number": 1,
                "characters": [{"name": "Henry"}],
                "visual_description": "Henry坐着看书",
            },
            {
                "frame_number": 2,
                "characters": [{"name": "Henry"}],
                "visual_description": "Henry站着伸懒腰",
            },
        ]
        results = validator.validate(base_state, mock_context)

        pose_warnings = [
            r
            for r in results
            if "pose" in r.message.lower() and r.severity == ValidationSeverity.WARNING
        ]
        assert len(pose_warnings) == 0

    def test_invalid_pose_transition_detected(
        self,
        validator: VisualContinuityValidator,
        base_state: PipelineState,
        mock_context: MagicMock,
    ) -> None:
        """Test detection of invalid pose transition."""
        base_state.frames = [
            {
                "frame_number": 1,
                "characters": [{"name": "Iris"}],
                "visual_description": "Iris躺着睡觉",
            },
            {
                "frame_number": 2,
                "characters": [{"name": "Iris"}],
                "visual_description": "Iris正在奔跑",
            },
        ]
        results = validator.validate(base_state, mock_context)

        pose_warnings = [
            r
            for r in results
            if "pose" in r.message.lower() and r.severity == ValidationSeverity.WARNING
        ]
        assert len(pose_warnings) > 0

    # ============================================
    # Composition Suggestion Tests
    # ============================================

    def test_composition_suggestions_generated(
        self,
        validator: VisualContinuityValidator,
        base_state: PipelineState,
        mock_context: MagicMock,
    ) -> None:
        """Test composition suggestion generation."""
        base_state.frames = [
            {
                "frame_number": 1,
                "description": "A simple scene",
            },
            {
                "frame_number": 2,
                "description": "Another scene",
            },
        ]
        results = validator.validate(base_state, mock_context)

        composition_info = [
            r
            for r in results
            if "composition" in r.message.lower()
            and r.severity == ValidationSeverity.INFO
        ]
        assert len(composition_info) > 0
        assert len(composition_info[0].suggestions) > 0

    def test_composition_with_thirds(
        self,
        validator: VisualContinuityValidator,
        base_state: PipelineState,
        mock_context: MagicMock,
    ) -> None:
        """Test composition when rule of thirds is mentioned."""
        base_state.frames = [
            {
                "frame_number": 1,
                "visual_description": "角色按三分法构图放置在画面右三分之一处",
            },
            {
                "frame_number": 2,
                "visual_description": "三分构图，主体在交叉点",
            },
        ]
        results = validator.validate(base_state, mock_context)

        composition_info = [
            r
            for r in results
            if "composition" in r.message.lower()
            and r.severity == ValidationSeverity.INFO
        ]

        # Should still have suggestions but not about rule of thirds
        if composition_info:
            for info in composition_info:
                thirds_suggestions = [
                    s for s in info.suggestions if "thirds" in s.lower()
                ]
                assert len(thirds_suggestions) == 0

    # ============================================
    # Dialogue-Visual Sync Tests
    # ============================================

    def test_dialogue_visual_sync_pass(
        self,
        validator: VisualContinuityValidator,
        base_state: PipelineState,
        mock_context: MagicMock,
    ) -> None:
        """Test dialogue-visual sync when speaking is indicated."""
        base_state.frames = [
            {
                "frame_number": 1,
                "beat_type": "dialogue",
                "dialogue": "你好",
                "characters": [{"name": "Jack"}],
                "visual_description": "Jack正在说话，嘴巴张开",
            },
        ]
        results = validator.validate(base_state, mock_context)

        sync_warnings = [
            r
            for r in results
            if "dialogue" in r.message.lower()
            and r.severity == ValidationSeverity.WARNING
        ]
        assert len(sync_warnings) == 0

    def test_dialogue_visual_sync_warning(
        self,
        validator: VisualContinuityValidator,
        base_state: PipelineState,
        mock_context: MagicMock,
    ) -> None:
        """Test dialogue-visual sync warning when speaking not indicated."""
        base_state.frames = [
            {
                "frame_number": 1,
                "beat_type": "dialogue",
                "dialogue": "你好，很高兴认识你",
                "characters": [{"name": "Kate"}],
                "visual_description": "Kate站在那里",
            },
            {
                "frame_number": 2,
                "beat_type": "dialogue",
                "dialogue": "我也很高兴",
                "characters": [{"name": "Kate"}],
                "visual_description": "Kate微笑着",
            },
        ]
        results = validator.validate(base_state, mock_context)

        sync_warnings = [
            r
            for r in results
            if "speaking" in r.message.lower()
            or "dialogue" in r.message.lower()
            and r.severity == ValidationSeverity.WARNING
        ]
        assert len(sync_warnings) > 0

    # ============================================
    # Helper Method Tests
    # ============================================

    def test_extract_visual_elements_costume(
        self, validator: VisualContinuityValidator
    ) -> None:
        """Test costume element extraction."""
        desc = "她穿着红色裙子，手里拿着包"
        elements = validator._extract_visual_elements(desc, "costume")
        assert len(elements) > 0

    def test_extract_visual_elements_hairstyle(
        self, validator: VisualContinuityValidator
    ) -> None:
        """Test hairstyle element extraction."""
        desc = "她有着长发，发色是黑色的"
        elements = validator._extract_visual_elements(desc, "hairstyle")
        assert len(elements) > 0

    def test_extract_position_chinese(
        self, validator: VisualContinuityValidator
    ) -> None:
        """Test Chinese position extraction."""
        assert validator._extract_position("站在画面左侧") == "left"
        assert validator._extract_position("在中央位置") == "center"
        assert validator._extract_position("在画面右边") == "right"

    def test_extract_position_english(
        self, validator: VisualContinuityValidator
    ) -> None:
        """Test English position extraction."""
        assert validator._extract_position("standing on the left") == "left"
        assert validator._extract_position("in the center") == "center"
        assert validator._extract_position("on the right side") == "right"

    def test_extract_pose(self, validator: VisualContinuityValidator) -> None:
        """Test pose extraction."""
        assert validator._extract_pose("他坐在椅子上") == "sitting"
        assert validator._extract_pose("她站着") == "standing"
        assert validator._extract_pose("he is running") == "running"

    def test_is_teleportation(self, validator: VisualContinuityValidator) -> None:
        """Test teleportation detection."""
        assert validator._is_teleportation("left", "right") is True
        assert validator._is_teleportation("left", "center") is False
        assert validator._is_teleportation("center", "center") is False
        assert validator._is_teleportation("foreground", "background") is True

    def test_can_auto_fix(self, validator: VisualContinuityValidator) -> None:
        """Test that auto-fix is disabled."""
        assert validator.can_auto_fix() is False

    # ============================================
    # Integration Tests
    # ============================================

    def test_full_validation_good_frames(
        self,
        validator: VisualContinuityValidator,
        base_state: PipelineState,
        mock_context: MagicMock,
    ) -> None:
        """Test full validation with well-formed frames."""
        base_state.frames = [
            {
                "frame_number": 1,
                "characters": [{"name": "Leo"}],
                "visual_description": "Leo穿着西装站在画面左侧，说话中",
                "beat_type": "dialogue",
                "dialogue": "你好",
            },
            {
                "frame_number": 2,
                "characters": [{"name": "Leo"}],
                "visual_description": "Leo穿着西装走到中央位置，开口说话",
                "beat_type": "dialogue",
                "dialogue": "很高兴见到你",
            },
            {
                "frame_number": 3,
                "characters": [{"name": "Leo"}],
                "visual_description": "Leo穿着西装站在中央，按三分法构图",
                "beat_type": "action",
            },
        ]
        results = validator.validate(base_state, mock_context)

        # Should have mostly success/info, minimal warnings
        error_count = sum(1 for r in results if not r.passed)
        assert error_count == 0

    def test_full_validation_multiple_issues(
        self,
        validator: VisualContinuityValidator,
        base_state: PipelineState,
        mock_context: MagicMock,
    ) -> None:
        """Test full validation with multiple issues."""
        base_state.frames = [
            {
                "frame_number": 1,
                "characters": [{"name": "Mia"}],
                "visual_description": "Mia穿着裙子站在左侧",
                "beat_type": "dialogue",
                "dialogue": "Hello",
            },
            {
                "frame_number": 2,
                "characters": [{"name": "Mia"}],
                "visual_description": "Mia穿着西装出现在右侧",
                "beat_type": "dialogue",
                "dialogue": "World",
            },
        ]
        results = validator.validate(base_state, mock_context)

        # Should detect costume inconsistency and teleportation
        warning_count = sum(
            1 for r in results if r.severity == ValidationSeverity.WARNING
        )
        assert warning_count >= 2
