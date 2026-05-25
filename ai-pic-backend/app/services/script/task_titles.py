"""Task title helpers for script pipeline jobs."""

from __future__ import annotations

from app.models.script import Episode, Script, Story


def friendly_task_title(
    prefix: str,
    script: Script,
    episode: Episode | None,
    story: Story | None,
) -> str:
    """Build a consistent task title with story/episode context."""
    story_label = ""
    if story and story.title:
        story_label = str(story.title)
    elif story:
        story_label = f"故事{story.id}"

    episode_label = ""
    if episode:
        ep_num = (
            f"第{episode.episode_number}集"
            if episode.episode_number is not None
            else f"剧集{episode.id}"
        )
        ep_title = f" {episode.title}" if episode.title else ""
        episode_label = f"{ep_num}{ep_title}"

    parts = [prefix]
    if story_label and episode_label:
        parts.append(f"{story_label} / {episode_label}")
    elif story_label:
        parts.append(story_label)
    elif episode_label:
        parts.append(episode_label)
    else:
        parts.append(f"剧本{script.id}")
    return " - ".join(parts)
