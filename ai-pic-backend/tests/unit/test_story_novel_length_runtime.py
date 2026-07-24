from types import SimpleNamespace

import pytest
from app.schemas.story_novel_export import StoryNovelGenerateRevisionRequest
from app.services.story.story_novel_chapter_service import sync_plan_chapter_runtime
from app.services.story.story_novel_task_guard import (
    NovelTaskCancelled,
    ensure_task_not_cancelled,
)


def test_runtime_fields_mirror_into_version_four_plan():
    revision = SimpleNamespace(
        generation_plan={
            "version": 4,
            "chapters": [{"position": 1, "title": "第一章"}],
        }
    )
    sync_plan_chapter_runtime(
        revision,
        1,
        {
            "status": "ready",
            "char_count": 3210,
            "context_hash": "context",
            "body_hash": "body",
            "source_hash": "source",
            "extraction_status": "ready",
            "event_ids": ["fact-1"],
            "memory_ids": ["memory-1"],
        },
    )
    row = revision.generation_plan["chapters"][0]
    assert row["actual_chars"] == 3210
    assert row["fact_ids"] == ["fact-1"]
    assert row["memory_ids"] == ["memory-1"]


def test_lightweight_task_guard_and_generate_compatibility():
    ensure_task_not_cancelled(None, SimpleNamespace(status="pending"))
    with pytest.raises(NovelTaskCancelled):
        ensure_task_not_cancelled(None, SimpleNamespace(status="cancelled"))
    request = StoryNovelGenerateRevisionRequest(target_words=200000, chapter_count=48)
    assert request.compatibility_warnings() == [
        "prose 已忽略旧字段: target_words, chapter_count"
    ]
