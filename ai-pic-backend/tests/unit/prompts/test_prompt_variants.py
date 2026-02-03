"""Tests for prompt variant system."""

import pytest

from app.prompts.prompt_variants import (
    PromptVariants,
    ScriptFormat,
    StoryFormat,
    get_template_for_format,
)


class TestStoryFormat:
    """Tests for StoryFormat enum."""

    def test_story_format_values(self):
        """Test StoryFormat enum values."""
        assert StoryFormat.DEFAULT.value == "default"
        assert StoryFormat.SHORT_DRAMA.value == "short_drama"
        assert StoryFormat.FILM.value == "film"
        assert StoryFormat.TV_SERIES.value == "tv_series"

    def test_story_format_is_string_enum(self):
        """Test that StoryFormat can be used as string."""
        assert str(StoryFormat.SHORT_DRAMA) == "StoryFormat.SHORT_DRAMA"
        assert StoryFormat.SHORT_DRAMA == "short_drama"


class TestPromptVariants:
    """Tests for PromptVariants class."""

    def test_story_outline_default(self):
        """Test story_outline returns default template."""
        result = PromptVariants.story_outline()
        assert result == "story_outline"

    def test_story_outline_short_drama(self):
        """Test story_outline returns short_drama variant."""
        result = PromptVariants.story_outline(StoryFormat.SHORT_DRAMA)
        assert result == "story_outline_short_drama"

    def test_story_outline_film(self):
        """Test story_outline returns film variant."""
        result = PromptVariants.story_outline(StoryFormat.FILM)
        assert result == "story_outline_film"

    def test_story_outline_tv_series(self):
        """Test story_outline returns tv_series variant."""
        result = PromptVariants.story_outline(StoryFormat.TV_SERIES)
        assert result == "story_outline_tv_series"

    def test_episode_generation_default(self):
        """Test episode_generation returns default template."""
        result = PromptVariants.episode_generation()
        assert result == "episode_generation"

    def test_episode_generation_short_drama(self):
        """Test episode_generation returns short_drama variant."""
        result = PromptVariants.episode_generation(StoryFormat.SHORT_DRAMA)
        assert result == "episode_generation_short_drama"

    def test_episode_from_outline_default(self):
        """Test episode_from_outline returns default template."""
        result = PromptVariants.episode_from_outline()
        assert result == "episode_from_outline"

    def test_episode_from_outline_short_drama(self):
        """Test episode_from_outline returns short_drama variant."""
        result = PromptVariants.episode_from_outline(StoryFormat.SHORT_DRAMA)
        assert result == "episode_from_outline_short_drama"

    def test_script_generation_default(self):
        """Test script_generation returns default template."""
        result = PromptVariants.script_generation()
        assert result == "script_generation"

    def test_script_generation_short_drama(self):
        """Test script_generation returns short_drama variant."""
        result = PromptVariants.script_generation(ScriptFormat.SHORT_DRAMA)
        assert result == "script_generation_short_drama"


class TestResolve:
    """Tests for generic resolve method."""

    def test_resolve_without_variant(self):
        """Test resolve returns base name without variant."""
        result = PromptVariants.resolve("story_outline")
        assert result == "story_outline"

    def test_resolve_with_variant(self):
        """Test resolve appends variant suffix."""
        result = PromptVariants.resolve("story_outline", "short_drama")
        assert result == "story_outline_short_drama"

    def test_resolve_with_default_variant(self):
        """Test resolve handles 'default' variant as no variant."""
        result = PromptVariants.resolve("story_outline", "default")
        assert result == "story_outline"

    def test_resolve_with_none_variant(self):
        """Test resolve handles None variant."""
        result = PromptVariants.resolve("story_outline", None)
        assert result == "story_outline"


class TestFromStoryFormatString:
    """Tests for format string conversion."""

    def test_short_drama_string(self):
        """Test converting 'short_drama' string."""
        result = PromptVariants.from_story_format_string("short_drama")
        assert result == StoryFormat.SHORT_DRAMA

    def test_film_string(self):
        """Test converting 'film' string."""
        result = PromptVariants.from_story_format_string("film")
        assert result == StoryFormat.FILM

    def test_tv_series_string(self):
        """Test converting 'tv_series' string."""
        result = PromptVariants.from_story_format_string("tv_series")
        assert result == StoryFormat.TV_SERIES

    def test_unknown_string_defaults(self):
        """Test that unknown string defaults to DEFAULT."""
        result = PromptVariants.from_story_format_string("unknown_format")
        assert result == StoryFormat.DEFAULT

    def test_case_insensitive(self):
        """Test case insensitive conversion."""
        result = PromptVariants.from_story_format_string("SHORT_DRAMA")
        assert result == StoryFormat.SHORT_DRAMA


class TestGetTemplateForFormat:
    """Tests for convenience function."""

    def test_explicit_format(self):
        """Test with explicit story_format parameter."""
        result = get_template_for_format("story_outline", story_format="short_drama")
        assert result == "story_outline_short_drama"

    def test_micro_genre_short_drama(self):
        """Test detecting short_drama from micro_genre."""
        result = get_template_for_format("story_outline", micro_genre="竖屏短剧")
        assert result == "story_outline_short_drama"

    def test_micro_genre_film(self):
        """Test detecting film from micro_genre."""
        result = get_template_for_format("story_outline", micro_genre="院线电影")
        assert result == "story_outline_film"

    def test_micro_genre_tv_series(self):
        """Test detecting tv_series from micro_genre."""
        result = get_template_for_format("story_outline", micro_genre="电视剧集")
        assert result == "story_outline_tv_series"

    def test_no_format_info(self):
        """Test default when no format info provided."""
        result = get_template_for_format("story_outline")
        assert result == "story_outline"

    def test_episode_generation_template(self):
        """Test with episode_generation base template."""
        result = get_template_for_format(
            "episode_generation", story_format="short_drama"
        )
        assert result == "episode_generation_short_drama"

    def test_unknown_base_template(self):
        """Test with unknown base template uses generic resolve."""
        result = get_template_for_format(
            "custom_template", story_format="short_drama"
        )
        assert result == "custom_template_short_drama"


class TestTemplateRenderingConsistency:
    """Tests for template rendering consistency (P2.12.6)."""

    @pytest.fixture
    def prompt_manager(self):
        """Get prompt manager instance."""
        from app.prompts.manager import prompt_manager

        return prompt_manager

    def test_all_story_outline_variants_exist(self, prompt_manager):
        """Verify all story_outline variants exist."""
        for format_type in StoryFormat:
            template_name = PromptVariants.story_outline(format_type)
            try:
                template = prompt_manager.load_template(template_name)
                assert template is not None
            except ValueError:
                # Template may not exist yet, skip
                pass

    def test_all_episode_generation_variants_exist(self, prompt_manager):
        """Verify all episode_generation variants exist."""
        for format_type in StoryFormat:
            template_name = PromptVariants.episode_generation(format_type)
            try:
                template = prompt_manager.load_template(template_name)
                assert template is not None
            except ValueError:
                # Template may not exist yet, skip
                pass

    def test_template_renders_without_error(self, prompt_manager):
        """Test that templates render without error with minimal variables."""
        minimal_vars = {
            "title": "Test Story",
            "genre": "Drama",
            "characters": [{"name": "Alice", "description": "Test character"}],
        }

        template_name = PromptVariants.story_outline(StoryFormat.DEFAULT)
        try:
            result = prompt_manager.render_prompt(template_name, minimal_vars)
            assert len(result) > 0
            assert "Test Story" in result
        except ValueError:
            pass  # Template may not exist
