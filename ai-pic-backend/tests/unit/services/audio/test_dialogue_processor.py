"""Unit tests for dialogue processing utilities."""

from unittest.mock import MagicMock

import pytest
from app.services.audio.dialogue_processor import (
    PlannedSegment,
    extract_dialogues_for_scene,
    extract_scene_number,
    extract_stage_for_scene,
    looks_like_silence,
    norm_name,
    plan_scene_segments,
    sanitize_dialogue_content,
)


class TestNormName:
    """Tests for norm_name function."""

    def test_basic_name(self):
        """Test basic name normalization."""
        assert norm_name("John Doe") == "johndoe"

    def test_name_with_extra_spaces(self):
        """Test name with extra whitespace."""
        assert norm_name("  John   Doe  ") == "johndoe"

    def test_uppercase_name(self):
        """Test uppercase name is lowercased."""
        assert norm_name("JOHN") == "john"

    def test_empty_string(self):
        """Test empty string."""
        assert norm_name("") == ""

    def test_none_value(self):
        """Test None value."""
        assert norm_name(None) == ""

    def test_chinese_name(self):
        """Test Chinese name."""
        assert norm_name("张 三") == "张三"


class TestLooksLikeSilence:
    """Tests for looks_like_silence function."""

    def test_empty_string(self):
        """Test empty string is silence."""
        assert looks_like_silence("") is True

    def test_whitespace_only(self):
        """Test whitespace only is silence."""
        assert looks_like_silence("   ") is True

    def test_ellipsis(self):
        """Test ellipsis is silence."""
        assert looks_like_silence("...") is True
        assert looks_like_silence("……") is True
        assert looks_like_silence("…") is True

    def test_silence_marker(self):
        """Test explicit silence markers."""
        assert looks_like_silence("（沉默）") is True
        assert looks_like_silence("(silence)") is True
        assert looks_like_silence("[silence]") is True

    def test_punctuation_only(self):
        """Test punctuation only is silence."""
        assert looks_like_silence("。。。") is True
        assert looks_like_silence("，，") is True

    def test_actual_text(self):
        """Test actual text is not silence."""
        assert looks_like_silence("Hello") is False
        assert looks_like_silence("你好") is False

    def test_none_value(self):
        """Test None is silence."""
        assert looks_like_silence(None) is True


class TestSanitizeDialogueContent:
    """Tests for sanitize_dialogue_content function."""

    def test_basic_text(self):
        """Test basic text without actions."""
        text, action = sanitize_dialogue_content("你好")
        assert text == "你好"
        assert action is None

    def test_leading_action(self):
        """Test leading inline action extraction."""
        text, action = sanitize_dialogue_content("（叹气）你好")
        assert text == "你好"
        assert action == "叹气"

    def test_trailing_action(self):
        """Test trailing inline action extraction."""
        text, action = sanitize_dialogue_content("你好（转身离开）")
        assert text == "你好"
        assert action == "转身离开"

    def test_both_actions(self):
        """Test both leading and trailing actions."""
        text, action = sanitize_dialogue_content("（叹气）你好（转身）")
        assert text == "你好"
        assert "叹气" in action
        assert "转身" in action

    def test_speech_attribution(self):
        """Test speech attribution extraction."""
        text, action = sanitize_dialogue_content("笑着说：你好")
        assert text == "你好"
        assert "笑着说" in action

    def test_existing_action(self):
        """Test preserving existing action."""
        text, action = sanitize_dialogue_content("你好", action="existing action")
        assert text == "你好"
        assert "existing action" in action

    def test_empty_content(self):
        """Test empty content."""
        text, action = sanitize_dialogue_content("")
        assert text == ""
        assert action is None


class TestExtractSceneNumber:
    """Tests for extract_scene_number function."""

    def test_integer_scene_number(self):
        """Test integer scene number."""
        scene = MagicMock()
        scene.scene_number = 5
        assert extract_scene_number(scene) == 5

    def test_string_scene_number(self):
        """Test string scene number."""
        scene = MagicMock()
        scene.scene_number = "3"
        assert extract_scene_number(scene) == 3

    def test_invalid_string(self):
        """Test invalid string returns 0."""
        scene = MagicMock()
        scene.scene_number = "invalid"
        assert extract_scene_number(scene) == 0

    def test_none_scene(self):
        """Test None scene returns 0."""
        assert extract_scene_number(None) == 0

    def test_none_scene_number(self):
        """Test None scene_number returns 0."""
        scene = MagicMock()
        scene.scene_number = None
        assert extract_scene_number(scene) == 0


class TestExtractDialoguesForScene:
    """Tests for extract_dialogues_for_scene function."""

    def test_basic_extraction(self):
        """Test basic dialogue extraction."""
        script = MagicMock()
        script.content = {
            "dialogues": [
                {"scene_number": 1, "character": "A", "content": "Hello"},
                {"scene_number": 2, "character": "B", "content": "World"},
                {"scene_number": 1, "character": "C", "content": "Hi"},
            ]
        }
        result = extract_dialogues_for_scene(script, 1)
        assert len(result) == 2
        assert result[0]["character"] == "A"
        assert result[1]["character"] == "C"

    def test_no_matching_scene(self):
        """Test no matching scene returns empty."""
        script = MagicMock()
        script.content = {
            "dialogues": [
                {"scene_number": 1, "content": "Hello"},
            ]
        }
        result = extract_dialogues_for_scene(script, 99)
        assert result == []

    def test_empty_dialogues(self):
        """Test empty dialogues list."""
        script = MagicMock()
        script.content = {"dialogues": []}
        result = extract_dialogues_for_scene(script, 1)
        assert result == []

    def test_none_content(self):
        """Test None content."""
        script = MagicMock()
        script.content = None
        result = extract_dialogues_for_scene(script, 1)
        assert result == []

    def test_none_script(self):
        """Test None script."""
        result = extract_dialogues_for_scene(None, 1)
        assert result == []


class TestExtractStageForScene:
    """Tests for extract_stage_for_scene function."""

    def test_basic_extraction(self):
        """Test basic stage direction extraction."""
        script = MagicMock()
        script.content = {
            "stage_directions": [
                {"scene_number": 1, "content": "Stage direction 1"},
                {"scene_number": 2, "content": "Stage direction 2"},
            ]
        }
        result = extract_stage_for_scene(script, 1)
        assert len(result) == 1
        assert result[0]["content"] == "Stage direction 1"

    def test_empty_stage_directions(self):
        """Test empty stage directions."""
        script = MagicMock()
        script.content = {"stage_directions": []}
        result = extract_stage_for_scene(script, 1)
        assert result == []


class TestPlannedSegment:
    """Tests for PlannedSegment dataclass."""

    def test_dialogue_segment(self):
        """Test creating dialogue segment."""
        seg = PlannedSegment(
            kind="dialogue",
            text="Hello",
            speaker_name="John",
            emotion="happy",
        )
        assert seg.kind == "dialogue"
        assert seg.text == "Hello"
        assert seg.speaker_name == "John"
        assert seg.emotion == "happy"

    def test_action_segment(self):
        """Test creating action segment."""
        seg = PlannedSegment(
            kind="action",
            text="Walking away",
            timing="end",
            planned_duration_ms=1000,
        )
        assert seg.kind == "action"
        assert seg.timing == "end"
        assert seg.planned_duration_ms == 1000

    def test_pause_segment(self):
        """Test creating pause segment."""
        seg = PlannedSegment(
            kind="pause",
            text="...",
            planned_duration_ms=500,
        )
        assert seg.kind == "pause"
        assert seg.planned_duration_ms == 500

    def test_frozen_dataclass(self):
        """Test that segment is immutable."""
        seg = PlannedSegment(kind="dialogue", text="Hello")
        with pytest.raises(AttributeError):
            seg.text = "World"


class TestPlanSceneSegments:
    """Tests for plan_scene_segments function."""

    def test_basic_dialogue_planning(self):
        """Test basic dialogue planning."""
        dialogues = [
            {"character": "A", "content": "Hello"},
            {"character": "B", "content": "World"},
        ]
        result = plan_scene_segments(dialogues=dialogues, stage_directions=[])

        # Should have dialogue + pause for each
        assert len(result) >= 2
        assert result[0].kind == "dialogue"
        assert result[0].speaker_name == "A"

    def test_stage_directions_at_start(self):
        """Test stage directions at scene start."""
        stage_directions = [
            {"content": "Opening action", "timing": "start"},
        ]
        result = plan_scene_segments(dialogues=[], stage_directions=stage_directions)

        assert len(result) >= 1
        assert result[0].kind == "action"
        assert result[0].timing == "start"

    def test_stage_directions_at_end(self):
        """Test stage directions at scene end."""
        stage_directions = [
            {"content": "Closing action", "timing": "end"},
        ]
        result = plan_scene_segments(dialogues=[], stage_directions=stage_directions)

        # End actions should be last
        assert result[-1].kind == "action"
        assert result[-1].timing == "end"

    def test_silence_becomes_pause(self):
        """Test that silence dialogue becomes pause."""
        dialogues = [
            {"character": "A", "content": "..."},
        ]
        result = plan_scene_segments(dialogues=dialogues, stage_directions=[])

        pause_segments = [s for s in result if s.kind == "pause"]
        assert len(pause_segments) >= 1

    def test_custom_pause_duration(self):
        """Test custom pause duration after dialogue."""
        dialogues = [{"character": "A", "content": "Hello"}]
        result = plan_scene_segments(
            dialogues=dialogues,
            stage_directions=[],
            pause_after_dialogue_ms=500,
        )

        pause_segments = [s for s in result if s.kind == "pause"]
        pause_with_duration = [
            s for s in pause_segments if s.planned_duration_ms == 500
        ]
        assert len(pause_with_duration) >= 1

    def test_empty_inputs(self):
        """Test empty dialogues and stage directions."""
        result = plan_scene_segments(dialogues=[], stage_directions=[])
        assert result == []

    def test_dialogue_with_emotion(self):
        """Test dialogue with emotion attribute."""
        dialogues = [
            {"character": "A", "content": "Hello", "emotion": "happy"},
        ]
        result = plan_scene_segments(dialogues=dialogues, stage_directions=[])

        dialogue_segments = [s for s in result if s.kind == "dialogue"]
        assert len(dialogue_segments) == 1
        assert dialogue_segments[0].emotion == "happy"

    def test_default_speaker_name(self):
        """Test default speaker name for missing character."""
        dialogues = [
            {"content": "Hello"},  # No character field
        ]
        result = plan_scene_segments(dialogues=dialogues, stage_directions=[])

        dialogue_segments = [s for s in result if s.kind == "dialogue"]
        assert dialogue_segments[0].speaker_name == "旁白"
