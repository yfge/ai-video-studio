import json

import pytest
from app.services.story.story_novel_canon_service import (
    normalize_canon,
    validate_generation_plan,
)
from app.services.story.story_novel_hard_context import build_hard_constraints
from tests.unit.test_story_novel_longform import _canon, _plan_row


def _future_timeline_canon(*, immutable: bool) -> dict:
    canon = _canon()
    canon["timeline"][0].update(
        {
            "label": "第48日，公开终局坐标",
            "story_time": "第48日",
            "immutable": immutable,
            "source_chapter_position": 48,
            "source_key_event": "第48日，公开终局坐标",
        }
    )
    return canon


def test_gate2_rejects_non_immutable_timeline():
    with pytest.raises(ValueError, match="gate2 timeline 必须 immutable"):
        normalize_canon(_future_timeline_canon(immutable=False))


def test_plan_rejects_future_timeline_even_if_raw_canon_bypasses_normalization():
    canon = _future_timeline_canon(immutable=False)
    chapter = _plan_row(1)

    with pytest.raises(ValueError, match="提前引用未来 timeline"):
        validate_generation_plan(canon, [chapter])


def test_hard_context_never_serializes_future_timeline_details():
    canon = _future_timeline_canon(immutable=False)
    chapter = _plan_row(1)
    hard = build_hard_constraints(
        snapshot={"title": "隔离测试"},
        canon=canon,
        chapter_plan=chapter,
        chapter_history=[chapter],
        approved_story_canon={},
        state_before={
            "subjects": {"char-a": {"location": "loc-gate", "status": "守规"}},
            "occurred_event_ids": [],
            "completed_milestone_ids": [],
            "threads": {},
        },
    )

    serialized = json.dumps(hard, ensure_ascii=False)
    assert "公开终局坐标" not in serialized
    assert "第48日" not in serialized
    assert "time-1" not in hard["chapter_contract"]["canon_refs"]
    assert hard["compiled_canon"]["timeline"] == []


def test_hard_context_keeps_current_chapter_timeline():
    canon = normalize_canon(_canon())
    chapter = _plan_row(1)
    hard = build_hard_constraints(
        snapshot={"title": "当前章"},
        canon=canon,
        chapter_plan=chapter,
        chapter_history=[chapter],
        approved_story_canon={},
        state_before={
            "subjects": {"char-a": {"location": "loc-gate", "status": "守规"}},
            "occurred_event_ids": [],
            "completed_milestone_ids": [],
            "threads": {},
        },
    )

    assert hard["chapter_contract"]["canon_refs"] == ["char-a", "time-1"]
    assert [item["id"] for item in hard["compiled_canon"]["timeline"]] == ["time-1"]
