import json

import pytest
from app.services.story.story_novel_canon_service import normalize_canon
from app.services.story.story_novel_context_utils import prompt_safe_prior_ledger
from app.services.story.story_novel_generation_context import build_chapter_context
from fastapi import HTTPException
from tests.unit.test_story_novel_canon_state import _v2_revision
from tests.unit.test_story_novel_longform import _canon, _plan_row, _setup


def test_hard_constraints_fail_instead_of_truncating(db_session):
    _user, _story, service, revision, _task, *_ = _setup(db_session)
    row = _plan_row()
    row["canon_refs"] = ["time-1"]
    canon_raw = _canon()
    canon_raw["world_rules"] = [
        {"id": "rule-huge", "statement": "不可删" * 12000, "exceptions": []}
    ]
    _v2_revision(revision, row)
    plan = dict(revision.generation_plan)
    canon = normalize_canon(canon_raw)
    plan.update(canon=canon, canon_hash=canon["canon_hash"])
    revision.generation_plan = plan
    db_session.commit()
    with pytest.raises(HTTPException) as exc:
        build_chapter_context(service, revision, 1, row)
    assert "不可截断 Canon 超过 32K" in str(exc.value.detail)


def test_prior_ledger_omits_full_state_snapshots_from_prose_context():
    safe = prompt_safe_prior_ledger(
        {
            "1": {
                "status": "ready",
                "state_after": {
                    "subjects": {
                        "char-future": {
                            "occupation": "FUTURE_IDENTITY_SECRET",
                        }
                    }
                },
                "gate_evidence": {"future_catalog": "FUTURE_EVENT_SECRET"},
                "state_delta": {"occurred_event_ids": ["event-current"]},
                "plot_delta": {"key_events": ["CURRENT_EVENT"]},
                "event_ids": ["fact-current"],
                "memory_ids": ["memory-current"],
                "state_after_hash": "state-hash",
            }
        }
    )
    prompt_evidence = json.dumps(safe, ensure_ascii=False)
    assert "state_after" not in safe["1"]
    assert "gate_evidence" not in safe["1"]
    assert "FUTURE_IDENTITY_SECRET" not in prompt_evidence
    assert "FUTURE_EVENT_SECRET" not in prompt_evidence
    assert safe["1"]["state_delta"]["occurred_event_ids"] == ["event-current"]
    assert safe["1"]["plot_delta"]["key_events"] == ["CURRENT_EVENT"]
    assert safe["1"]["event_ids"] == ["fact-current"]
    assert safe["1"]["memory_ids"] == ["memory-current"]
    assert safe["1"]["state_after_hash"] == "state-hash"


def test_chapter_context_exposes_only_current_outline_contract(db_session):
    _user, _story, service, revision, _task, *_ = _setup(db_session)
    current = _plan_row(1)
    current["canon_refs"] = ["time-1"]
    current["preconditions"] = [
        {
            "subject_id": "char-a",
            "field": "status",
            "operator": "eq",
            "value": "守规",
        },
        {
            "subject_id": "char-a",
            "field": "rank",
            "operator": "eq",
            "value": "守门人",
        },
    ]
    future = {
        **_plan_row(2),
        "title": "FUTURE_CHAPTER_TITLE",
        "goal": "FUTURE_EVENT_SECRET",
        "key_events": ["FUTURE_EVENT_SECRET"],
    }
    canon_raw = _canon()
    canon_raw["entities"][0]["aliases"] = ["FUTURE_CURRENT_ALIAS"]
    canon_raw["entities"][0]["attributes"] = {
        "rank": "守门人",
        "hidden_identity": "CURRENT_ENTITY_FUTURE_SECRET",
        "terminal_state": "CURRENT_ENTITY_TERMINAL_SECRET",
    }
    canon_raw["world_rules"] = [
        {
            "id": "rule-current",
            "statement": "KEEP_CURRENT_WORLD_INVARIANT",
            "exceptions": [],
        },
        {
            "id": "rule-global",
            "statement": "KEEP_SECOND_GLOBAL_WORLD_INVARIANT",
            "exceptions": [],
        },
    ]
    canon_raw["initial_state"]["char-a"]["hidden_identity"] = "INITIAL_STATE_SECRET"
    canon_raw["character_arcs"][0]["checkpoints"] = [
        {"position": 2, "state": "FUTURE_ARC_SECRET"}
    ]
    canon_raw["character_arcs"][0]["end_state"] = "FUTURE_END_SECRET"
    canon_raw["entities"].append(
        {
            "id": "char-future",
            "kind": "character",
            "name": "FUTURE_NAMED_CHARACTER",
            "aliases": ["FUTURE_CHARACTER_ALIAS"],
            "attributes": {},
        }
    )
    canon = normalize_canon(canon_raw)
    revision.generation_plan = {
        "schema": "story_novel_generation_plan.v2",
        "version": 2,
        "status": "ready",
        "canon": canon,
        "canon_hash": canon["canon_hash"],
        "chapter_count": 2,
        "target_chars": 6000,
        "chapters": [current, future],
    }
    snapshot = dict(revision.story_snapshot)
    snapshot["main_characters"] = ["FUTURE_MAIN_CHARACTER"]
    snapshot["character_relationships"] = ["FUTURE_RELATIONSHIP"]
    snapshot["theme"] = "UNSCOPED_STORY_METADATA_SECRET"
    snapshot["setting_time"] = "STATIC_STORY_TIME"
    snapshot["setting_location"] = "STATIC_STORY_LOCATION"
    snapshot["world_building"] = "主角会在海啸钟响后背叛盟友"
    snapshot["story_seed"] = {
        **dict(snapshot["story_seed"]),
        "premise": "FUTURE_PREMISE_SECRET",
        "central_conflict": "FUTURE_CONFLICT_SECRET",
        "outline": "CURRENT_EVENT then FUTURE_EVENT_SECRET",
        "outline_text": "CURRENT_EVENT then FUTURE_EVENT_SECRET",
        "ending_direction": "FUTURE_END_SECRET",
        "world_constraints": ["UNSCOPED_WORLD_CONSTRAINT_SECRET"],
        "content_constraints": [
            "STATIC_CONTENT_CONSTRAINT",
            "不得提前揭露 FUTURE_NAMED_CHARACTER 的身份",
            "第 2 章前不得让盐梁桥断裂",
        ],
        "protagonists": [
            {
                "virtual_ip_business_id": "future",
                "initial_state": "FUTURE_PROTAGONIST_SECRET",
            }
        ],
        "structured_outline": {
            "chapters": [
                {"position": 1, "title": "CURRENT_CHAPTER_TITLE"},
                {"position": 2, "title": "FUTURE_CHAPTER_TITLE"},
            ]
        },
    }
    revision.story_snapshot = snapshot
    revision.chapter_count = 2
    db_session.commit()
    context = build_chapter_context(service, revision, 1, current)["context"]
    prompt_evidence = json.dumps(context, ensure_ascii=False)
    assert context["hard_constraints"]["chapter_contract"]["position"] == 1
    assert "FUTURE_CHAPTER_TITLE" not in prompt_evidence
    assert "FUTURE_EVENT_SECRET" not in prompt_evidence
    assert "FUTURE_ARC_SECRET" not in prompt_evidence
    assert "FUTURE_END_SECRET" not in prompt_evidence
    assert "FUTURE_PREMISE_SECRET" not in prompt_evidence
    assert "FUTURE_CONFLICT_SECRET" not in prompt_evidence
    assert "FUTURE_MAIN_CHARACTER" not in prompt_evidence
    assert "FUTURE_RELATIONSHIP" not in prompt_evidence
    assert "FUTURE_NAMED_CHARACTER" not in prompt_evidence
    assert "FUTURE_CHARACTER_ALIAS" not in prompt_evidence
    assert "FUTURE_CURRENT_ALIAS" not in prompt_evidence
    assert "FUTURE_PROTAGONIST_SECRET" not in prompt_evidence
    assert "char-future" not in prompt_evidence
    assert "CURRENT_ENTITY_FUTURE_SECRET" not in prompt_evidence
    assert "CURRENT_ENTITY_TERMINAL_SECRET" not in prompt_evidence
    assert "主角会在海啸钟响后背叛盟友" not in prompt_evidence
    assert "UNSCOPED_WORLD_CONSTRAINT_SECRET" not in prompt_evidence
    assert "STATIC_STORY_TIME" not in prompt_evidence
    assert "STATIC_STORY_LOCATION" not in prompt_evidence
    assert "STATIC_CONTENT_CONSTRAINT" in prompt_evidence
    assert "不得提前揭露" not in prompt_evidence
    assert "第 2 章前" not in prompt_evidence
    assert (
        context["hard_constraints"]["story_invariants"]["story_seed"][
            "future_constraint_count_excluded"
        ]
        == 2
    )
    assert "INITIAL_STATE_SECRET" not in prompt_evidence
    assert "KEEP_CURRENT_WORLD_INVARIANT" in prompt_evidence
    assert "KEEP_SECOND_GLOBAL_WORLD_INVARIANT" in prompt_evidence
    assert (
        context["hard_constraints"]["current_state"]["subjects"]["char-a"]["status"]
        == "守规"
    )
    assert (
        context["hard_constraints"]["current_state"]["subjects"]["char-a"]["rank"]
        == "守门人"
    )
    assert (
        "attributes" not in context["hard_constraints"]["compiled_canon"]["entities"][0]
    )
