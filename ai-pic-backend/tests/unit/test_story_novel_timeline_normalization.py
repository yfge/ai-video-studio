import pytest
from app.services.story.story_novel_canon_service import (
    normalize_canon,
    validate_generation_plan,
)
from app.services.story.story_novel_timeline_contract import compile_timeline_bindings
from tests.unit.test_story_novel_longform import _canon, _plan_row


def test_compiler_keeps_unknown_refs_visible_to_fail_closed_validation():
    canon = normalize_canon(_canon())
    row = _plan_row(1)
    row["canon_refs"] = ["canon-1", "char-a"]
    row["timeline_event_bindings"] = {"time-1": "invented-event"}

    compiled = compile_timeline_bindings(canon, [row])

    assert compiled[0]["canon_refs"] == ["canon-1", "char-a", "time-1"]
    assert compiled[0]["timeline_event_bindings"] == {"time-1": "event-1"}
    with pytest.raises(ValueError, match="引用未知 Canon"):
        validate_generation_plan(canon, compiled)


def test_compiler_derives_exact_binding_for_known_refs():
    canon = normalize_canon(_canon())
    row = _plan_row(1)
    row["canon_refs"] = ["char-a"]
    row["timeline_event_bindings"] = {"time-1": "invented-event"}

    compiled = compile_timeline_bindings(canon, [row])

    assert compiled[0]["canon_refs"] == ["char-a", "time-1"]
    assert compiled[0]["timeline_event_bindings"] == {"time-1": "event-1"}
    validate_generation_plan(canon, compiled)


def test_compiler_cannot_invent_binding_when_source_event_is_missing():
    canon = normalize_canon(_canon())
    row = _plan_row(1)
    row["key_events"] = ["完全不同的事件"]
    row["canon_refs"] = ["canon-1"]

    compiled = compile_timeline_bindings(canon, [row])

    assert compiled[0]["canon_refs"] == ["canon-1"]
    assert compiled[0]["timeline_event_bindings"] == {}
    with pytest.raises(ValueError, match="引用未知 Canon"):
        validate_generation_plan(canon, compiled)
