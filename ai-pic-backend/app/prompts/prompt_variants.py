"""Type-safe prompt variant system.

Provides a clean interface for calling prompt templates with different variants
(e.g., story_outline for short_drama, film, tv_series) without string manipulation.

Usage:
    from app.prompts.prompt_variants import PromptVariants, StoryFormat

    # Get the template name for a specific format
    template = PromptVariants.story_outline(StoryFormat.SHORT_DRAMA)
    # Returns: "story_outline_short_drama"

    # Or use with prompt manager directly
    prompt = prompt_manager.render_prompt(
        PromptVariants.story_outline(format_type),
        variables
    )
"""

from enum import Enum
from typing import Optional


class StoryFormat(str, Enum):
    """Story format types for template selection."""

    DEFAULT = "default"
    SHORT_DRAMA = "short_drama"
    FILM = "film"
    TV_SERIES = "tv_series"


class ScriptFormat(str, Enum):
    """Script format types for template selection."""

    DEFAULT = "default"
    SHORT_DRAMA = "short_drama"
    FILM = "film"
    DOCUMENTARY = "documentary"


class ImageStyle(str, Enum):
    """Image generation style types."""

    REALISTIC = "realistic"
    ANIME = "anime"
    CARTOON = "cartoon"
    CINEMATIC = "cinematic"


class PromptVariants:
    """Type-safe prompt variant resolver.

    Instead of building template names with string concatenation,
    use this class to get the correct template name for a given variant.
    """

    # Template base names and their supported variants
    _TEMPLATES = {
        "story_outline": {
            StoryFormat.DEFAULT: "story_outline",
            StoryFormat.SHORT_DRAMA: "story_outline_short_drama",
            StoryFormat.FILM: "story_outline_film",
            StoryFormat.TV_SERIES: "story_outline_tv_series",
        },
        "episode_generation": {
            StoryFormat.DEFAULT: "episode_generation",
            StoryFormat.SHORT_DRAMA: "episode_generation_short_drama",
            StoryFormat.FILM: "episode_generation_film",
            StoryFormat.TV_SERIES: "episode_generation_tv_series",
        },
        "episode_from_outline": {
            StoryFormat.DEFAULT: "episode_from_outline",
            StoryFormat.SHORT_DRAMA: "episode_from_outline_short_drama",
        },
        "episode_duration_reject": {
            StoryFormat.DEFAULT: "episode_duration_reject",
            StoryFormat.SHORT_DRAMA: "episode_duration_reject_short_drama",
        },
        "script_generation": {
            ScriptFormat.DEFAULT: "script_generation",
            ScriptFormat.SHORT_DRAMA: "script_generation_short_drama",
        },
    }

    @classmethod
    def story_outline(cls, format_type: StoryFormat = StoryFormat.DEFAULT) -> str:
        """Get story outline template name for the given format.

        Args:
            format_type: The story format (short_drama, film, tv_series, or default)

        Returns:
            Template name string

        Example:
            >>> PromptVariants.story_outline(StoryFormat.SHORT_DRAMA)
            'story_outline_short_drama'
        """
        return cls._TEMPLATES["story_outline"].get(format_type, "story_outline")

    @classmethod
    def episode_generation(cls, format_type: StoryFormat = StoryFormat.DEFAULT) -> str:
        """Get episode generation template name for the given format.

        Args:
            format_type: The story format

        Returns:
            Template name string
        """
        return cls._TEMPLATES["episode_generation"].get(format_type, "episode_generation")

    @classmethod
    def episode_from_outline(cls, format_type: StoryFormat = StoryFormat.DEFAULT) -> str:
        """Get episode from outline template name for the given format.

        Args:
            format_type: The story format

        Returns:
            Template name string
        """
        return cls._TEMPLATES["episode_from_outline"].get(
            format_type, "episode_from_outline"
        )

    @classmethod
    def episode_duration_reject(
        cls, format_type: StoryFormat = StoryFormat.DEFAULT
    ) -> str:
        """Get episode duration reject template name for the given format.

        Args:
            format_type: The story format

        Returns:
            Template name string
        """
        return cls._TEMPLATES["episode_duration_reject"].get(
            format_type, "episode_duration_reject"
        )

    @classmethod
    def script_generation(cls, format_type: ScriptFormat = ScriptFormat.DEFAULT) -> str:
        """Get script generation template name for the given format.

        Args:
            format_type: The script format

        Returns:
            Template name string
        """
        return cls._TEMPLATES["script_generation"].get(
            format_type, "script_generation"
        )

    @classmethod
    def resolve(cls, base_name: str, variant: Optional[str] = None) -> str:
        """Generic resolver for any template with optional variant.

        Args:
            base_name: The base template name (e.g., "story_outline")
            variant: Optional variant suffix (e.g., "short_drama")

        Returns:
            Full template name

        Example:
            >>> PromptVariants.resolve("story_outline", "short_drama")
            'story_outline_short_drama'
            >>> PromptVariants.resolve("story_outline")
            'story_outline'
        """
        if variant and variant != "default":
            return f"{base_name}_{variant}"
        return base_name

    @classmethod
    def from_story_format_string(cls, format_str: str) -> StoryFormat:
        """Convert a string to StoryFormat enum.

        Args:
            format_str: Format string like "short_drama", "film", etc.

        Returns:
            Corresponding StoryFormat enum value
        """
        format_map = {
            "short_drama": StoryFormat.SHORT_DRAMA,
            "film": StoryFormat.FILM,
            "tv_series": StoryFormat.TV_SERIES,
            "default": StoryFormat.DEFAULT,
        }
        return format_map.get(format_str.lower(), StoryFormat.DEFAULT)


def get_template_for_format(
    base_template: str,
    story_format: Optional[str] = None,
    micro_genre: Optional[str] = None,
) -> str:
    """Convenience function to get template name based on story format.

    This function is commonly used in agent code to determine which
    template variant to use based on the story's format or micro_genre.

    Args:
        base_template: Base template name (e.g., "story_outline")
        story_format: Explicit format string (e.g., "short_drama")
        micro_genre: Alternative source for format detection

    Returns:
        Template name to use

    Example:
        >>> get_template_for_format("story_outline", story_format="short_drama")
        'story_outline_short_drama'
        >>> get_template_for_format("story_outline", micro_genre="竖屏短剧")
        'story_outline_short_drama'
    """
    # Determine format from explicit format or micro_genre
    format_type = StoryFormat.DEFAULT

    if story_format:
        format_type = PromptVariants.from_story_format_string(story_format)
    elif micro_genre:
        # Detect format from micro_genre keywords
        micro_lower = micro_genre.lower()
        if any(kw in micro_lower for kw in ["短剧", "short", "竖屏"]):
            format_type = StoryFormat.SHORT_DRAMA
        elif any(kw in micro_lower for kw in ["电影", "film", "movie"]):
            format_type = StoryFormat.FILM
        elif any(kw in micro_lower for kw in ["电视", "剧集", "series"]):
            format_type = StoryFormat.TV_SERIES

    # Use the appropriate resolver based on base template
    if base_template == "story_outline":
        return PromptVariants.story_outline(format_type)
    elif base_template == "episode_generation":
        return PromptVariants.episode_generation(format_type)
    elif base_template == "episode_from_outline":
        return PromptVariants.episode_from_outline(format_type)
    elif base_template == "episode_duration_reject":
        return PromptVariants.episode_duration_reject(format_type)
    else:
        return PromptVariants.resolve(base_template, format_type.value)
