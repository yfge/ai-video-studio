import json

from tests.unit.test_story_novel_canon_state import _body, _delta
from tests.unit.test_story_novel_longform import _plan_row


def typed_audit_payload(quote: str, premature: list[str]) -> str:
    event_ids = ["event-1", *premature]
    return json.dumps(
        {
            "occurred_event_ids": ["event-1"],
            "premature_future_event_ids": premature,
            "state_transitions": [],
            "knowledge_grants": [],
            "location_transitions": [],
            "milestones_consumed": [],
            "opened_thread_ids": [],
            "resolved_thread_ids": [],
            "world_rule_violations": [],
            "evidence": {event_id: quote for event_id in event_ids},
            "timeline_evidence": {},
        },
        ensure_ascii=False,
    )


def plan_without_timeline() -> dict:
    plan = _plan_row(1)
    plan["canon_refs"] = ["char-a"]
    plan["timeline_event_bindings"] = {}
    return plan


def body_with_current_timeline() -> str:
    payload = json.loads(_body())
    payload["content_text"] = "第一日，" + payload["content_text"]
    return json.dumps(payload, ensure_ascii=False)


def delta_with_current_timeline() -> str:
    payload = json.loads(_delta())
    event_quote = payload["evidence"]["event-1"]
    payload["timeline_evidence"] = {"time-1": f"第一日，{event_quote}"}
    return json.dumps(payload, ensure_ascii=False)
