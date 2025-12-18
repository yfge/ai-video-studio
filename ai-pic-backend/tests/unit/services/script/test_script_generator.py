"""
Unit tests for Script Generator Service.

Tests the ScriptGenerator class for AI-powered script generation.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from app.services.script.script_generator import ScriptGenerator, get_script_generator
from app.core.exceptions import NotFoundError, GenerationFailedError


class TestScriptGenerator:
    """Tests for ScriptGenerator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_session = MagicMock()
        self.generator = ScriptGenerator(self.mock_session)

    def test_init(self):
        """Test generator initialization."""
        assert self.generator.session == self.mock_session
        assert self.generator.episode_repo is not None
        assert self.generator.story_repo is not None
        assert self.generator.prompt_manager is not None

    def test_get_user_id_filter_admin(self):
        """Test admin user returns None for filter."""
        mock_user = MagicMock()
        mock_user.is_admin = True
        mock_user.is_superuser = False

        result = self.generator._get_user_id_filter(mock_user)
        assert result is None

    def test_get_user_id_filter_regular_user(self):
        """Test regular user returns their ID for filter."""
        mock_user = MagicMock()
        mock_user.is_admin = False
        mock_user.is_superuser = False
        mock_user.id = 123

        result = self.generator._get_user_id_filter(mock_user)
        assert result == 123

    def test_parse_ai_result_dict(self):
        """Test parsing dict result."""
        result = {"content": {"scenes": []}}
        parsed = self.generator._parse_ai_result(result)
        assert parsed == {"scenes": []}

    def test_parse_ai_result_string(self):
        """Test parsing string result."""
        with patch("app.services.script.script_generator.extract_json_block") as mock_extract:
            mock_extract.return_value = {"scenes": []}
            result = {"content": '{"scenes": []}'}
            parsed = self.generator._parse_ai_result(result)
            assert parsed == {"scenes": []}

    def test_normalize_scenes_empty(self):
        """Test normalizing empty scenes."""
        result = self.generator._normalize_scenes([])
        assert result == []

    def test_normalize_scenes_dict(self):
        """Test normalizing dict scenes."""
        raw = [{"scene_number": 1, "description": "Test scene"}]
        result = self.generator._normalize_scenes(raw)
        assert len(result) == 1
        assert result[0]["scene_number"] == 1
        assert result[0]["description"] == "Test scene"

    def test_normalize_scenes_string(self):
        """Test normalizing string scenes."""
        raw = ["Scene description"]
        result = self.generator._normalize_scenes(raw)
        assert len(result) == 1
        assert result[0]["scene_number"] == 1
        assert result[0]["description"] == "Scene description"

    def test_normalize_dialogues_empty(self):
        """Test normalizing empty dialogues."""
        result = self.generator._normalize_dialogues([], [])
        assert result == []

    def test_normalize_dialogues_string(self):
        """Test normalizing string dialogues."""
        scenes = [{"scene_number": 1}]
        raw = ["Dialog line"]
        result = self.generator._normalize_dialogues(raw, scenes)
        assert len(result) == 1
        assert result[0]["content"] == "Dialog line"
        assert result[0]["scene_number"] == 1

    def test_normalize_dialogues_dict(self):
        """Test normalizing dict dialogues."""
        scenes = [{"scene_number": 1}]
        raw = [{"content": "Dialog line", "character": "Alice"}]
        result = self.generator._normalize_dialogues(raw, scenes)
        assert len(result) == 1
        assert result[0]["content"] == "Dialog line"

    def test_normalize_stage_directions_empty(self):
        """Test normalizing empty stage directions."""
        result = self.generator._normalize_stage_directions([], [])
        assert result == []

    def test_normalize_stage_directions_string(self):
        """Test normalizing string stage directions."""
        scenes = [{"scene_number": 1}]
        raw = ["Stage direction"]
        result = self.generator._normalize_stage_directions(raw, scenes)
        assert len(result) == 1
        assert result[0]["content"] == "Stage direction"

    def test_build_extra_metadata(self):
        """Test building extra metadata."""
        ai_content = {"custom_field": "value", "content": "ignored"}
        result_data = {
            "generation_method": "test",
            "provider_used": "openai",
        }
        metadata = self.generator._build_extra_metadata(ai_content, result_data)
        assert "custom_field" in metadata
        assert "content" not in metadata
        assert "agent_run" in metadata
        assert metadata["agent_run"]["generation_method"] == "test"

    @patch.object(ScriptGenerator, '_get_user_id_filter')
    def test_preview_prompt(self, mock_filter):
        """Test preview prompt generation."""
        mock_filter.return_value = None
        mock_user = MagicMock()
        mock_episode = MagicMock()
        mock_episode.episode_number = 1
        mock_episode.title = "Test Episode"
        mock_story = MagicMock()
        mock_story.id = 1
        mock_story.main_characters = []
        mock_episode.story = mock_story

        self.generator.episode_repo.get_with_story = MagicMock(return_value=mock_episode)
        self.generator.prompt_manager.render_prompt = MagicMock(return_value="Test prompt")

        with patch("app.services.script.script_generator.collect_previous_episode_summaries", return_value=[]):
            with patch("app.services.script.script_generator.build_character_profiles", return_value=[]):
                with patch("app.services.script.script_generator.build_episode_data", return_value={}):
                    with patch("app.services.script.script_generator.build_story_data", return_value={}):
                        result = self.generator.preview_prompt(
                            episode_id=1,
                            user=mock_user,
                        )
                        assert result == "Test prompt"

    @patch.object(ScriptGenerator, '_get_user_id_filter')
    def test_preview_prompt_not_found(self, mock_filter):
        """Test preview prompt with non-existent episode."""
        mock_filter.return_value = None
        mock_user = MagicMock()

        self.generator.episode_repo.get_with_story = MagicMock(return_value=None)

        with pytest.raises(NotFoundError):
            self.generator.preview_prompt(episode_id=999, user=mock_user)


class TestGetScriptGenerator:
    """Tests for get_script_generator factory function."""

    def test_creates_generator(self):
        """Test factory creates generator instance."""
        mock_session = MagicMock()
        generator = get_script_generator(mock_session)
        assert isinstance(generator, ScriptGenerator)
        assert generator.session == mock_session
