import json
from types import SimpleNamespace

import anyio
from app.services.story.story_novel_plan_semantic_audit import (
    audit_and_patch_plan_batch,
)


def _canon():
    return {
        "entities": [
            {"id": "char-a", "kind": "character", "name": "甲"},
            {"id": "loc-a", "kind": "location", "name": "甲地"},
            {"id": "loc-b", "kind": "location", "name": "乙地"},
        ],
        "timeline": [],
        "world_rules": [],
        "milestones": [],
        "character_arcs": [],
        "initial_state": {"char-a": {"location": "loc-a", "knowledge": []}},
    }


def _chapter(position, event_id, movements=None, milestones=None):
    return {
        "position": position,
        "title": f"第{position}章",
        "goal": "移动",
        "key_events": ["甲前往乙地"],
        "character_focus": ["甲"],
        "open_threads": [],
        "end_state": "抵达",
        "preconditions": [],
        "required_event_ids": [event_id],
        "state_transitions": [],
        "knowledge_grants": [],
        "location_transitions": list(movements or []),
        "milestones_consumed": list(milestones or []),
        "forbidden_event_ids": [],
        "payoffs_due": [],
        "canon_refs": ["char-a", "loc-a", "loc-b"],
        "timeline_event_bindings": {},
    }


def _movement():
    return {
        "subject_id": "char-a",
        "from_location_id": "loc-a",
        "to_location_id": "loc-b",
        "means": "步行",
    }


def _audit(position, event_id, movements=None):
    return {
        "events": [
            {
                "position": position,
                "event_id": event_id,
                "execution_contract": {
                    "event_id": event_id,
                    "action_phase": "instant",
                    "time_scope": "instant",
                    "actor_ids": ["char-a"],
                    "effort": "light",
                    "timeline_ids": [],
                    "knowledge_fact_ids": [],
                },
                "feasibility_issues": [],
                "missing_effects": {
                    "knowledge_grants": [],
                    "state_transitions": [],
                    "location_transitions": list(movements or []),
                    "milestones_consumed": [],
                },
            }
        ]
    }


def test_semantic_audit_drops_movement_when_subject_already_at_target():
    calls = 0

    async def generate(_revision, _prompt, **_kwargs):
        nonlocal calls
        calls += 1
        return json.dumps(_audit(2, "ev-2", [_movement()]), ensure_ascii=False)

    async def run():
        return await audit_and_patch_plan_batch(
            SimpleNamespace(generation_plan={}),
            contract={"story_seed": {"schema": "story_seed_v2"}},
            canon=_canon(),
            prior_chapters=[_chapter(1, "ev-1", [_movement()])],
            batch_chapters=[_chapter(2, "ev-2")],
            require_complete=False,
            generate_text=generate,
        )

    result = anyio.run(run)
    assert calls == 1
    assert result[0]["location_transitions"] == []


def test_semantic_audit_keeps_executable_missing_movement():
    responses = iter((_audit(1, "ev-1", [_movement()]), _audit(1, "ev-1")))

    async def generate(_revision, _prompt, **_kwargs):
        return json.dumps(next(responses), ensure_ascii=False)

    async def run():
        return await audit_and_patch_plan_batch(
            SimpleNamespace(generation_plan={}),
            contract={"story_seed": {"schema": "story_seed_v2"}},
            canon=_canon(),
            prior_chapters=[],
            batch_chapters=[_chapter(1, "ev-1")],
            require_complete=False,
            generate_text=generate,
        )

    result = anyio.run(run)
    assert result[0]["location_transitions"] == [_movement()]


def test_semantic_reaudit_drops_exact_existing_milestone():
    canon = _canon()
    canon["milestones"] = [
        {
            "id": "mile-1",
            "label": "抵达",
            "outcomes": [],
            "repeatable": False,
            "planned_position": 1,
        }
    ]
    calls = 0

    async def generate(_revision, _prompt, **_kwargs):
        nonlocal calls
        calls += 1
        payload = _audit(1, "ev-1")
        payload["events"][0]["missing_effects"]["milestones_consumed"] = ["mile-1"]
        return json.dumps(payload, ensure_ascii=False)

    async def run():
        return await audit_and_patch_plan_batch(
            SimpleNamespace(generation_plan={}),
            contract={"story_seed": {"schema": "story_seed_v2"}},
            canon=canon,
            prior_chapters=[],
            batch_chapters=[_chapter(1, "ev-1", milestones=["mile-1"])],
            require_complete=True,
            generate_text=generate,
        )

    result = anyio.run(run)
    assert calls == 1
    assert result[0]["milestones_consumed"] == ["mile-1"]
