from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Optional


_FORMAT_AWARE_TEMPLATES = {
    "story_outline",
    "system_prompt_story",
    "system_prompt_script",
    "episode_generation",
    "script_scenes",
}

_SUPPORTED_STORY_FORMATS = {"tv_series", "film"}


def _extract_story_format(variables: Mapping[str, Any]) -> Optional[str]:
    candidate = variables.get("story_format")
    if isinstance(candidate, str) and candidate.strip():
        return candidate.strip()

    story = variables.get("story")
    if isinstance(story, Mapping):
        candidate = story.get("story_format")
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()

    episode = variables.get("episode")
    if isinstance(episode, Mapping):
        candidate = episode.get("story_format")
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()

    return None


def resolve_template_name(
    template_name: str, variables: Mapping[str, Any], prompts_dir: Path
) -> str:
    """Resolve a base template to a story_format-specific variant if available."""
    story_format = _extract_story_format(variables)
    if not story_format or story_format not in _SUPPORTED_STORY_FORMATS:
        return template_name

    if template_name not in _FORMAT_AWARE_TEMPLATES:
        return template_name

    candidate = f"{template_name}_{story_format}"
    if (prompts_dir / f"{candidate}.txt").exists():
        return candidate

    return template_name

