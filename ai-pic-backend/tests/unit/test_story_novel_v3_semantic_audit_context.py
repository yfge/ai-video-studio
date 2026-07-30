import json
from types import SimpleNamespace

import anyio
from app.services.story.story_novel_expected_delta import compile_expected_delta
from app.services.story.story_novel_future_guard_index import compile_future_guard_index
from app.services.story.story_novel_v3_audit_semantics import (
    current_state_contract,
    future_state_boundaries,
)
from app.services.story.story_novel_v3_evaluation import _audit_once
from app.services.story.story_novel_v3_gate import prose_violations


def _current():
    return {
        "position": 6,
        "title": "试种契",
        "goal": "完成当日试种",
        "key_events": ["沈禾按试种契完成三亩小畦田的整地"],
        "required_event_ids": ["event-6"],
        "canon_refs": ["char-he", "loc-trial-field"],
        "execution_contracts": [{"event_id": "event-6", "actor_ids": ["char-he"]}],
        "state_transitions": [],
        "location_transitions": [],
        "knowledge_grants": [],
        "milestones_consumed": [],
        "open_threads": [],
        "payoffs_due": [],
        "timeline_event_bindings": {},
        "min_chars": 10,
        "target_chars": 20,
        "max_chars": 100,
    }


def _future():
    return {
        "position": 8,
        "title": "不得进入审计边界的未来标题",
        "goal": "不得进入审计边界的未来目标",
        "key_events": ["刘岩交出水契木牌，沈禾正式取得东渠一成引水权"],
        "required_event_ids": ["event-8"],
        "canon_refs": ["char-he", "obj-water-slip"],
        "state_transitions": [
            {
                "subject_id": "char-he",
                "field": "permissions",
                "from_value": ["perm-trial"],
                "to_value": ["perm-trial", "perm-east-canal-share"],
            }
        ],
        "location_transitions": [],
        "knowledge_grants": [],
        "milestones_consumed": [],
        "open_threads": [],
        "payoffs_due": [],
        "timeline_event_bindings": {},
    }


def _canon():
    return {
        "entities": [
            {"id": "char-he", "kind": "character", "name": "沈禾", "aliases": []},
            {
                "id": "loc-trial-field",
                "kind": "location",
                "name": "三亩小畦田",
                "aliases": [],
            },
            {
                "id": "obj-water-slip",
                "kind": "object",
                "name": "水契木牌",
                "aliases": [],
            },
        ],
        "world_rules": [{"id": "rule-water", "statement": "引水权须经水契转移"}],
        "timeline": [],
    }


def _state():
    return {
        "subjects": {
            "char-he": {
                "permissions": ["perm-trial"],
                "location": "loc-trial-field",
            }
        },
        "threads": {},
        "occurred_event_ids": [],
        "completed_milestone_ids": [],
    }


def test_audit_context_exposes_current_truth_and_future_permission_boundary():
    current = _current()
    expected = compile_expected_delta(current, _state())
    plan = {"canon": _canon(), "chapters": [current, _future()]}

    current_truth = current_state_contract(_canon(), current, expected, _state())
    boundaries = future_state_boundaries(plan, current, expected, _state())

    assert current_truth["subjects"][0]["state"]["permissions"] == ["perm-trial"]
    assert boundaries == [
        {
            "boundary_id": "state:8:1",
            "kind": "state_transition",
            "first_allowed_position": 8,
            "subject_id": "char-he",
            "name": "沈禾",
            "aliases": [],
            "entity_kind": "character",
            "field": "permissions",
            "from_value": ["perm-trial"],
            "to_value": ["perm-trial", "perm-east-canal-share"],
        }
    ]
    surface = json.dumps(boundaries, ensure_ascii=False)
    assert "未来标题" not in surface
    assert "未来目标" not in surface
    assert "刘岩交出水契木牌" not in surface


def test_v3_prose_gate_leaves_date_entity_and_world_semantics_to_auditor():
    current = _current()
    revision = SimpleNamespace(generation_plan={"canon": _canon(), "chapters": []})
    prose = {
        "char_count": 30,
        "content_text": "八月三日，岑野说东渠引水权已经归沈禾。",
    }

    assert prose_violations(revision, current, prose) == []


def test_pipeline_sends_permission_boundary_only_to_audit_prompt():
    current, future, canon, state = _current(), _future(), _canon(), _state()
    expected = compile_expected_delta(current, state)
    plan = {
        "canon": canon,
        "chapters": [current, future],
        "future_guard_index": compile_future_guard_index(
            [current, future], entities=canon["entities"]
        ),
    }
    revision = SimpleNamespace(generation_plan=plan)
    prompts = []

    async def generate(_revision, prompt, **_kwargs):
        prompts.append(prompt)
        return json.dumps(
            {
                "proofs": [{"contract_id": "event:event-6", "sentence_ids": ["S0001"]}],
                "unexpected_claims": [],
                "future_hits": [],
                "world_rule_hits": [],
            },
            ensure_ascii=False,
        )

    async def run():
        return await _audit_once(
            revision,
            6,
            current,
            {"beats": []},
            {
                "state_before": state,
                "hard_constraints": {"compiled_canon": canon},
                "brief_input": {"prior_ledger": {}},
            },
            {"content_text": "试种契上写着沈禾已有权引东渠水。"},
            expected,
            [{"sentence_id": "S0001", "text": "试种契上写着沈禾已有权引东渠水。"}],
            generate,
            "audit.6",
            1,
            None,
        )

    anyio.run(run)
    assert "future_state_boundaries" in prompts[0]
    assert "perm-east-canal-share" in prompts[0]
    assert "当前状态值" in prompts[0]
    assert "不得进入审计边界的未来标题" not in prompts[0]
    assert "不得进入审计边界的未来目标" not in prompts[0]
    assert "刘岩交出水契木牌" not in prompts[0]
