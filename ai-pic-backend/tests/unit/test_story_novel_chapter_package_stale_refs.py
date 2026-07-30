import json
from types import SimpleNamespace

from app.services.story import story_novel_chapter_package_contract as package_contract


def test_parser_strips_derived_location_before_service_manifest(monkeypatch):
    skeleton = {
        "position": 1,
        "title": "签约",
        "goal": "签署契书",
        "key_events": ["主角签署契书"],
        "character_focus": ["主角"],
        "open_threads": [],
        "end_state": "契书生效",
        "min_chars": 2000,
        "target_chars": 2500,
        "max_chars": 3000,
        "length_source": "profile_default",
        "length": {"min_chars": 2000, "target_chars": 2500, "max_chars": 3000},
        "required_event_ids": ["event-1-1"],
        "timeline_event_bindings": {},
        "milestones_consumed": [],
        "forbidden_event_ids": [],
        "payoffs_due": [],
        "canon_refs": ["object-contract"],
        "future_guard_entity_ids": ["object-contract"],
    }
    model_transition = {
        "subject_id": "object-contract",
        "field": "location",
        "from_value": None,
        "to_value": "loc-home",
        "reason": "随签约落到主角住处",
    }
    payload = {
        "chapter_contract": {
            **skeleton,
            "preconditions": [],
            "state_transitions": [model_transition],
            "location_transitions": [],
            "knowledge_grants": [],
            "execution_contracts": [],
        },
        "chapter_brief": {},
    }
    captured = {}

    def parse_plan(text, *_args, **_kwargs):
        return {"chapters": json.loads(text)["chapters"]}, None

    def finalize(row, *_args, **_kwargs):
        captured.update(row=row)
        return row

    monkeypatch.setattr(package_contract, "parse_plan", parse_plan)
    monkeypatch.setattr(package_contract, "_finalize_contract", finalize)
    monkeypatch.setattr(
        package_contract,
        "build_v3_planning_context",
        lambda *_args, **_kwargs: {"brief_input": {}},
    )
    monkeypatch.setattr(package_contract, "_bound_brief", lambda *_args: {})
    revision = SimpleNamespace(
        generation_plan={"chapters": [skeleton], "canon": {}, "thread_payoffs": []}
    )

    package_contract.parse_chapter_package(
        json.dumps(payload, ensure_ascii=False),
        object(),
        revision,
        1,
        package_input={"state_before": None},
    )

    assert captured["row"]["state_transitions"] == []


def test_service_manifest_excludes_removed_location_and_keeps_milestone_effects():
    skeleton = {
        "position": 1,
        "title": "签约",
        "goal": "签署契书",
        "key_events": ["主角签署契书"],
        "character_focus": ["主角"],
        "open_threads": [],
        "end_state": "契书生效",
        "target_chars": 2500,
        "required_event_ids": ["event-1-1"],
        "timeline_event_bindings": {},
        "milestones_consumed": ["mile-1"],
    }
    execution = {
        "event_id": "event-1-1",
        "action_phase": "instant",
        "time_scope": "same_day",
        "actor_ids": ["char-main"],
        "effort": "light",
        "timeline_ids": [],
        "knowledge_fact_ids": [],
    }
    row = {
        **skeleton,
        "state_transitions": [],
        "location_transitions": [],
        "knowledge_grants": [],
        "execution_contracts": [execution],
    }
    canon = {
        "entities": [
            {"id": "char-main", "kind": "character", "name": "主角"},
            {"id": "object-contract", "kind": "object", "name": "契书"},
        ],
        "milestones": [
            {
                "id": "mile-1",
                "outcomes": [
                    {
                        "subject_id": "char-main",
                        "field": "permissions",
                        "operator": "contains",
                        "value": "trial-right",
                    },
                    {
                        "subject_id": "object-contract",
                        "field": "status",
                        "operator": "eq",
                        "value": "signed",
                    },
                    {
                        "subject_id": "object-contract",
                        "field": "owner_id",
                        "operator": "eq",
                        "value": "char-main",
                    },
                ],
            }
        ],
    }
    result = package_contract._finalize_contract(row, skeleton, canon)

    refs = {item["effect_ref"] for item in result["effect_manifest"]["items"]}
    assert "state:1" not in refs
    assert refs == {
        "milestone:mile-1:char-main:permissions",
        "milestone:mile-1:object-contract:status",
        "milestone:mile-1:object-contract:owner_id",
    }
