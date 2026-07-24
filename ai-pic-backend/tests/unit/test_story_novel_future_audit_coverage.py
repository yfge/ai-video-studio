import json

from app.services.story.story_novel_state_extraction import _validation_result
from tests.unit.story_novel_future_audit_fixtures import plan_without_timeline


def _payload(audit):
    return json.dumps(
        {
            "occurred_event_ids": [],
            "premature_future_event_ids": [],
            "future_event_audit": audit,
        },
        ensure_ascii=False,
    )


def test_future_audit_must_cover_every_catalog_event():
    catalog = [
        {
            "position": 2,
            "events": [
                {"event_id": "event-2-a", "description": "未来事件甲"},
                {"event_id": "event-2-b", "description": "未来事件乙"},
            ],
        }
    ]

    _normalized, error, issues = _validation_result(
        _payload({"event-2-a": "not_present"}),
        chapter_plan=plan_without_timeline(),
        content_text="本章没有发生未来事件。",
        current_timeline=[],
        future_event_catalog=catalog,
    )

    assert "未完整覆盖未来事件目录" in error
    assert issues[0]["code"] == "canon_violation"


def test_future_audit_accepts_exact_catalog_coverage():
    catalog = [
        {
            "position": 2,
            "events": [{"event_id": "event-2", "description": "未来事件"}],
        }
    ]

    normalized, error, issues = _validation_result(
        _payload({"event-2": "not_present"}),
        chapter_plan=plan_without_timeline(),
        content_text="本章没有发生未来事件。",
        current_timeline=[],
        future_event_catalog=catalog,
    )

    assert error is None
    assert issues == []
    assert normalized["future_event_audit"] == {"event-2": "not_present"}
