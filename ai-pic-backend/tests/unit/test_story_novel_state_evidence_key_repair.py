import json

import anyio
from app.services.story.story_novel_state_extraction import (
    _validation_result,
    extract_chapter_state,
)
from tests.unit.test_story_novel_state_evidence_patch import BODY, _initial_delta


def test_location_field_is_repaired_as_typed_delta_contract_not_quote_only():
    delta = {
        **_initial_delta(),
        "state_transitions": [
            {
                "subject_id": "char-a",
                "field": "location",
                "from_value": "loc-a",
                "to_value": "loc-b",
                "reason": "下船",
            }
        ],
        "timeline_evidence": {},
    }

    _normalized, error, issues = _validation_result(
        json.dumps(delta, ensure_ascii=False),
        chapter_plan={},
        content_text=BODY,
        current_timeline=[],
        future_event_catalog=[],
    )

    assert "location 不能写入 state_transitions: char-a" in error
    assert any(item["code"] == "canon_violation" for item in issues)


def test_quote_only_repair_removes_invented_timeline_evidence_id():
    initial = {
        **_initial_delta(),
        "timeline_evidence": {"invented-time": "2174年8月4日……采样完成"},
    }
    calls = 0

    async def generate(_revision, prompt, **_kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            return json.dumps(initial, ensure_ascii=False)
        assert "timeline_evidence 必须是空对象" in prompt
        return json.dumps(
            {"evidence": initial["evidence"], "timeline_evidence": {}},
            ensure_ascii=False,
        )

    async def run():
        return await extract_chapter_state(
            object(),
            chapter_plan={
                "required_event_ids": ["event-2-1"],
                "canon_refs": [],
                "timeline_event_bindings": {},
            },
            state_before={},
            content_text=BODY,
            future_event_catalog=[],
            current_timeline=[],
            generate_text=generate,
        )

    result, repair_count = anyio.run(run)

    assert calls == 2
    assert repair_count == 1
    assert result["timeline_evidence"] == {}
    assert result["state_transitions"] == initial["state_transitions"]
