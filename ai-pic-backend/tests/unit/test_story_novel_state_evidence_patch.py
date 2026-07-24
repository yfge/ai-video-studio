import json

import anyio
import pytest
from app.services.story.story_novel_state_extraction import (
    StateExtractionError,
    extract_chapter_state,
)

BODY = (
    "2174年8月4日，澄砂港的清晨比往常来得更早。"
    "她把采样管探入水面，小心地收集了约五毫升的水样。"
    "她拧紧管盖，贴上标签，用记号笔写下编号：R-17。"
    "然后从背包里取出一个标准的物证筒。"
)
EVENT_QUOTE = (
    "她把采样管探入水面，小心地收集了约五毫升的水样。"
    "……她拧紧管盖，贴上标签，用记号笔写下编号：R-17。"
)


def _initial_delta() -> dict:
    return {
        "occurred_event_ids": ["event-2-1"],
        "premature_future_event_ids": [],
        "state_transitions": [
            {
                "subject_id": "r-17-sample",
                "field": "status",
                "from_value": "未采集",
                "to_value": "已采集",
                "reason": "正文采样",
            }
        ],
        "knowledge_grants": [],
        "location_transitions": [],
        "milestones_consumed": [],
        "opened_thread_ids": [],
        "resolved_thread_ids": [],
        "world_rule_violations": [],
        "evidence": {"event-2-1": EVENT_QUOTE},
        "timeline_evidence": {"time-3": "2174年8月4日……她用记号笔写下编号：R-17。"},
    }


def test_quote_only_repair_freezes_typed_state_and_excludes_future_catalog():
    prompts = []
    parameters = []

    async def generate(_revision, prompt, **kwargs):
        prompts.append(prompt)
        parameters.append(kwargs)
        if len(prompts) == 1:
            return json.dumps(_initial_delta(), ensure_ascii=False)
        return json.dumps(
            {
                "evidence": {"event-2-1": EVENT_QUOTE},
                "timeline_evidence": {"time-3": f"2174年8月4日……{EVENT_QUOTE}"},
            },
            ensure_ascii=False,
        )

    async def run():
        return await extract_chapter_state(
            object(),
            chapter_plan={
                "position": 2,
                "title": "红尘落在水面",
                "key_events": ["采集 R-17"],
                "required_event_ids": ["event-2-1"],
                "canon_refs": ["time-3"],
                "timeline_event_bindings": {"time-3": "event-2-1"},
            },
            state_before={"SECRET_STATE_BEFORE": True},
            content_text=BODY,
            future_event_catalog=[{"description": "FUTURE_EVENT_SECRET"}],
            current_timeline=[
                {
                    "id": "time-3",
                    "label": "R-17 红尘采样",
                    "story_time": "2174年8月4日",
                    "immutable": True,
                }
            ],
            generate_text=generate,
        )

    result, repair_count = anyio.run(run)

    assert repair_count == 1
    assert result["state_transitions"] == _initial_delta()["state_transitions"]
    assert result["timeline_evidence"]["time-3"] == (f"2174年8月4日……{EVENT_QUOTE}")
    assert "FUTURE_EVENT_SECRET" in prompts[0]
    assert "FUTURE_EVENT_SECRET" not in prompts[1]
    assert "SECRET_STATE_BEFORE" not in prompts[1]
    assert "opened_thread_ids 必须逐项原样返回" in prompts[0]
    assert "只判断当前章合同" in prompts[0]
    assert parameters[1]["max_tokens"] == 3000


def test_quote_only_repair_rejects_attempted_state_change():
    calls = 0

    async def generate(_revision, _prompt, **_kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            return json.dumps(_initial_delta(), ensure_ascii=False)
        return json.dumps(
            {
                "state_transitions": [],
                "evidence": {"event-2-1": EVENT_QUOTE},
                "timeline_evidence": {"time-3": f"2174年8月4日……{EVENT_QUOTE}"},
            },
            ensure_ascii=False,
        )

    async def run():
        return await extract_chapter_state(
            object(),
            chapter_plan={
                "canon_refs": ["time-3"],
                "required_event_ids": ["event-2-1"],
                "timeline_event_bindings": {"time-3": "event-2-1"},
            },
            state_before={},
            content_text=BODY,
            future_event_catalog=[],
            current_timeline=[
                {
                    "id": "time-3",
                    "story_time": "2174年8月4日",
                    "immutable": True,
                }
            ],
            generate_text=generate,
        )

    with pytest.raises(StateExtractionError, match="只能返回 evidence"):
        anyio.run(run)
