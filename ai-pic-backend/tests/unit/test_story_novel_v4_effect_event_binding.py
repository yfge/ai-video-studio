import json

from app.services.story.story_novel_chapter_contract_v4 import compile_intent_contract
from app.services.story.story_novel_chapter_intent import parse_chapter_intent
from app.services.story.story_novel_context_utils import value_hash
from tests.unit.test_story_novel_v4_effect_intents import _effect
from tests.unit.test_story_novel_v4_snapshot import _response, _skeleton, _snapshot


def test_fact_knowledge_uses_the_intent_event_that_establishes_the_fact():
    snapshot = _snapshot()
    snapshot["handle_bindings"]["events"]["E02"] = "event-1-2"
    snapshot["handle_bindings"]["entities"]["X01"] = "fact-answer"
    snapshot["model_input"]["current_chapter"]["events"].append(
        {"event_handle": "E02", "description": "众人执行后续试验"}
    )
    snapshot["model_input"]["allowed_entity_handles"].append("X01")
    snapshot["model_input"]["visible_characters_and_world"].append(
        {
            "entity_handle": "X01",
            "kind": "fact",
            "name": "旧账答案",
            "aliases": [],
            "attributes": {},
            "current_state": {"status": "unresolved"},
        }
    )
    snapshot["execution_context"]["state_before"]["subjects"].update(
        {"char-real-id": {"knowledge": []}, "fact-answer": {"status": "unresolved"}}
    )
    snapshot["state_before_hash"] = value_hash(
        snapshot["execution_context"]["state_before"]
    )
    snapshot["execution_context"]["evidence"]["state_before_hash"] = snapshot[
        "state_before_hash"
    ]
    snapshot["model_input_hash"] = value_hash(snapshot["model_input"])
    snapshot.pop("snapshot_hash")
    snapshot["snapshot_hash"] = value_hash(snapshot)

    payload = json.loads(_response())
    payload["beats"][-1]["event_handles"] = ["E01", "E02"]
    payload["effect_intents"] = [
        _effect("FX01", "status_change", "X01", value="resolved")
    ]
    skeleton = {
        **_skeleton(),
        "required_event_ids": ["event-1-1", "event-1-2"],
        "key_events": ["查明旧账", "执行后续试验"],
        "milestones_consumed": ["mile-answer"],
    }
    canon = {
        "entities": [],
        "milestones": [
            {
                "id": "mile-answer",
                "outcomes": [
                    {
                        "subject_id": "char-real-id",
                        "field": "knowledge",
                        "operator": "contains",
                        "value": "fact-answer",
                    }
                ],
            }
        ],
    }

    intent = parse_chapter_intent(json.dumps(payload, ensure_ascii=False), snapshot)
    contract, brief, _delta = compile_intent_contract(skeleton, intent, snapshot, canon)

    assert contract["knowledge_grants"] == [
        {
            "character_id": "char-real-id",
            "fact_id": "fact-answer",
            "source_event_id": "event-1-1",
        }
    ]
    assert contract["effect_event_bindings"]["state:1"] == "event-1-1"
    assert contract["effect_event_bindings"]["knowledge:1"] == "event-1-1"
    assert "knowledge:1" in brief["beats"][-1]["effect_contract_ids"]
