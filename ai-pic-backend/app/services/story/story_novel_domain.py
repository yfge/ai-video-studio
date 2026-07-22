from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

from app.models.script import Story
from app.models.story_novel_export import StoryNovelChapter, StoryNovelExport


def sha256_text(value: str) -> str:
    return hashlib.sha256((value or "").encode("utf-8")).hexdigest()


def build_story_snapshot(story: Story) -> dict[str, Any]:
    """Freeze the creative contract; episodes are intentionally excluded."""
    return {
        "business_id": story.business_id,
        "title": story.title,
        "story_format": story.story_format,
        "genre": story.genre,
        "theme": story.theme,
        "target_audience": story.target_audience,
        "premise": story.premise,
        "synopsis": story.synopsis,
        "main_conflict": story.main_conflict,
        "resolution": story.resolution,
        "main_characters": story.main_characters,
        "character_relationships": story.character_relationships,
        "setting_time": story.setting_time,
        "setting_location": story.setting_location,
        "world_building": story.world_building,
        "captured_at": datetime.utcnow().isoformat(),
    }


def default_generation_plan(story: Story, chapter_count: int) -> dict[str, Any]:
    chapters = [
        {
            "position": index,
            "title": f"第{index}章",
            "goal": f"推进《{story.title}》的核心冲突与角色弧",
        }
        for index in range(1, chapter_count + 1)
    ]
    return {"version": 1, "chapter_count": chapter_count, "chapters": chapters}


def active_chapters(revision: StoryNovelExport) -> list[StoryNovelChapter]:
    return sorted(
        [row for row in revision.chapters if not row.is_deleted],
        key=lambda row: row.position,
    )


def materialize_content(revision: StoryNovelExport) -> str:
    return "\n\n".join(
        f"# {chapter.title}\n\n{chapter.content_text.strip()}"
        for chapter in active_chapters(revision)
        if chapter.content_text.strip()
    )


def refresh_revision_content(revision: StoryNovelExport) -> None:
    revision.content_text = materialize_content(revision)
    revision.total_words = len("".join(revision.content_text.split()))
    revision.content_hash = sha256_text(revision.content_text)


def compact_chapter_context(revision: StoryNovelExport, before: int) -> list[dict]:
    return [
        {
            "position": row.position,
            "title": row.title,
            "summary": row.summary or row.content_text[:500],
            "cliffhanger": row.cliffhanger,
            "content_hash": row.content_hash,
        }
        for row in active_chapters(revision)
        if row.position < before
    ][-4:]


def json_prompt_payload(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
