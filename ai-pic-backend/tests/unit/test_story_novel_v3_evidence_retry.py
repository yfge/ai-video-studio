import json

import anyio
import pytest
from app.services.story import story_novel_v3_prompts as prompts
from app.services.story.story_novel_chapter_brief_contract import (
    compile_chapter_brief_input,
)
from app.services.story.story_novel_chapter_service import generate_or_resume_chapter
from app.services.story.story_novel_future_guard_index import compile_future_guard_index
from app.services.story.story_novel_length_service import generation_plan_hash
from app.services.story.story_novel_state_service import initial_story_state
from fastapi import HTTPException
from tests.unit.story_novel_v3_test_support import persisted_stage_text
from tests.unit.test_story_novel_longform import _setup
from tests.unit.test_story_novel_v3_pipeline import _blocks, _brief, _canon, _row


def test_evidence_only_retry_reaudits_without_rewriting_prose(db_session):
    _user, _story, service, revision, task, *_ = _setup(db_session, with_character=True)
    row = _row()
    canon = _canon()
    future = compile_future_guard_index([row], canon["milestones"], canon["entities"])
    plan = {
        "schema": "story_novel_generation_plan.v3",
        "version": 4,
        "status": "ready",
        "phase": "ready",
        "outline_hash": "outline-v3",
        "model_policy": {
            "planning_model": "deepseek:planning",
            "prose_model": "deepseek:prose",
            "audit_model": "deepseek:audit",
        },
        "planning_contract_version": 3,
        "event_execution_contract_version": 1,
        "state_compiler_version": 1,
        "future_guard_index": future,
        "future_guard_hash": future["index_hash"],
        "canon": canon,
        "canon_hash": canon["canon_hash"],
        "canon_gate_version": 2,
        "chapter_count": 1,
        "chapters": [row],
    }
    plan["plan_hash"] = generation_plan_hash(plan)
    revision.generation_plan = plan
    revision.continuity_ledger = {
        "schema": "story_novel_continuity.v4",
        "state_status": "empty",
        "chapters": {},
    }
    revision.chapter_count = 1
    db_session.commit()
    calls = []
    invocation_id = 200

    async def generate(_revision, _prompt, *, stage, **_kwargs):
        nonlocal invocation_id
        invocation_id += 1
        calls.append(stage)
        if stage.startswith("chapter_planning"):
            source = compile_chapter_brief_input(
                row,
                initial_story_state(canon),
                allowed_entity_ids=["char-a", "loc-gate"],
            )
            payload = _brief(source)
        elif stage.startswith("prose"):
            payload = {"blocks": _blocks(8)}
        else:
            proofs = (
                [{"contract_id": "event:event-1", "sentence_ids": ["S0001"]}]
                if ".evidence_retry" in stage
                else []
            )
            payload = {
                "proofs": proofs,
                "unexpected_claims": [],
                "future_hits": [],
                "world_rule_hits": [],
            }
        return persisted_stage_text(
            db_session,
            revision,
            stage,
            json.dumps(payload, ensure_ascii=False),
            invocation_id,
        )

    anyio.run(generate_or_resume_chapter, service, revision, task, row, generate)

    assert calls[:2] == ["chapter_planning.1", "prose.1"]
    assert len(calls) == 4
    assert calls[2].startswith("audit.1.")
    assert ".evidence_retry." in calls[3]
    assert all(not stage.startswith("local_repair") for stage in calls)
    assert revision.continuity_ledger["chapters"]["1"]["status"] == "ready"


def test_evidence_only_resume_reuses_body_and_accumulates_audits(db_session):
    _user, _story, service, revision, task, *_ = _setup(db_session, with_character=True)
    row = _row()
    canon = _canon()
    future = compile_future_guard_index([row], canon["milestones"], canon["entities"])
    plan = {
        "schema": "story_novel_generation_plan.v3",
        "version": 4,
        "status": "ready",
        "phase": "ready",
        "outline_hash": "outline-v3",
        "model_policy": {
            "planning_model": "deepseek:planning",
            "prose_model": "deepseek:prose",
            "audit_model": "deepseek:audit",
        },
        "planning_contract_version": 3,
        "event_execution_contract_version": 1,
        "state_compiler_version": 1,
        "future_guard_index": future,
        "future_guard_hash": future["index_hash"],
        "canon": canon,
        "canon_hash": canon["canon_hash"],
        "canon_gate_version": 2,
        "chapter_count": 1,
        "chapters": [row],
    }
    plan["plan_hash"] = generation_plan_hash(plan)
    revision.generation_plan = plan
    revision.continuity_ledger = {
        "schema": "story_novel_continuity.v4",
        "state_status": "empty",
        "chapters": {},
    }
    revision.chapter_count = 1
    db_session.commit()
    calls = []
    audit_passes = False
    invocation_id = 300

    async def generate(_revision, _prompt, *, stage, **_kwargs):
        nonlocal invocation_id
        invocation_id += 1
        calls.append(stage)
        if stage.startswith("chapter_planning"):
            source = compile_chapter_brief_input(
                row,
                initial_story_state(canon),
                allowed_entity_ids=["char-a", "loc-gate"],
            )
            payload = _brief(source)
        elif stage.startswith("prose"):
            payload = {"blocks": _blocks(8)}
        else:
            proofs = (
                [{"contract_id": "event:event-1", "sentence_ids": ["S0001"]}]
                if audit_passes
                else []
            )
            payload = {
                "proofs": proofs,
                "unexpected_claims": [],
                "future_hits": [],
                "world_rule_hits": [],
            }
        return persisted_stage_text(
            db_session,
            revision,
            stage,
            json.dumps(payload, ensure_ascii=False),
            invocation_id,
        )

    with pytest.raises(HTTPException, match="v3 门禁失败"):
        anyio.run(generate_or_resume_chapter, service, revision, task, row, generate)
    first_hash = revision.chapters[0].content_hash
    entry = revision.continuity_ledger["chapters"]["1"]
    assert entry["status"] == "audit"
    assert entry["audit_failure_kind"] == "evidence_only"
    assert calls.count("prose.1") == 1

    audit_passes = True
    calls.clear()
    anyio.run(generate_or_resume_chapter, service, revision, task, row, generate)
    assert len(calls) == 1
    assert calls[0].startswith("audit.1.")
    assert revision.chapters[0].content_hash == first_hash
    attempts = revision.continuity_ledger["chapters"]["1"]["stage_metrics"]["audit"][
        "attempts"
    ]
    assert len(attempts) == 3

    exhausted = dict(revision.continuity_ledger["chapters"]["1"])
    exhausted.update(
        status="audit",
        stage="audit",
        audit_failure_kind="evidence_only",
        state_validation={"status": "failed", "violations": []},
    )
    ledger = dict(revision.continuity_ledger)
    ledger["chapters"] = {"1": exhausted}
    revision.continuity_ledger = ledger
    db_session.commit()
    calls.clear()
    anyio.run(generate_or_resume_chapter, service, revision, task, row, generate)
    assert calls == []
    recovered = revision.continuity_ledger["chapters"]["1"]
    assert recovered["status"] == "ready"
    assert recovered["proof_spans"]
    assert revision.chapters[0].content_hash == first_hash


def test_evidence_retry_prompt_requires_semantic_proof_change():
    focus = (
        "角色获知证据早于来源事件: knowledge:1 最早 S0067，"
        "来源 event:event-11-1 最早 S0074"
    )
    prompt = prompts.chapter_audit_prompt(
        {
            "proof_contracts": [],
            "sentence_index": [],
            "repair_focus": [focus],
        }
    )

    assert focus in prompt
    assert "原样返回上一轮违规的 sentence_ids 视为失败" in prompt
    assert "sentence_id 的前后大小不能单独证明或否定因果关系" in prompt
    assert "由同一事件过程获知事实" in prompt
    assert "知识 proof 的首句不得早于" not in prompt
