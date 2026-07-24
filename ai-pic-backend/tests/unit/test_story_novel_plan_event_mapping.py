import pytest
from app.services.story.story_novel_plan_diagnostics import _diagnose_events
from app.services.story.story_novel_plan_validator import _validate_events


def test_required_event_ids_map_one_to_one_to_structured_key_events():
    chapter = {
        "key_events": ["发现入口", "取得钥匙"],
        "forbidden_event_ids": [],
    }
    context = {"seen_events": set()}

    with pytest.raises(ValueError, match="不一一对应"):
        _validate_events(chapter, 1, ["event-1"], context)

    errors = []
    _diagnose_events(chapter, 1, ["event-1"], context, errors)
    assert errors == ["第 1 章 required_event_ids 与 key_events 不一一对应"]
