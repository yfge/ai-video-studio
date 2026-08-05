import json

import anyio
from app.services.story.story_novel_canon_service import normalize_canon
from app.services.story.story_novel_chapter_brief_contract import (
    BRIEF_SCHEMA,
    compile_chapter_brief_input,
)
from app.services.story.story_novel_chapter_service import generate_or_resume_chapter
from app.services.story.story_novel_future_guard_index import compile_future_guard_index
from app.services.story.story_novel_length_service import generation_plan_hash
from app.services.story.story_novel_state_service import initial_story_state
from tests.unit.story_novel_v3_test_support import persisted_stage_text
from tests.unit.test_story_novel_longform import _setup


def _row():
    return {
        "position": 1,
        "title": "第一章",
        "goal": "发现线索",
        "key_events": ["第一日，长篇主角发现线索"],
        "character_focus": ["长篇主角"],
        "open_threads": [],
        "end_state": "主角决定追查",
        "min_chars": 3000,
        "target_chars": 3200,
        "max_chars": 5000,
        "preconditions": [],
        "required_event_ids": ["event-1"],
        "state_transitions": [],
        "knowledge_grants": [],
        "location_transitions": [],
        "milestones_consumed": [],
        "forbidden_event_ids": [],
        "payoffs_due": [],
        "canon_refs": ["char-a", "loc-gate"],
        "timeline_event_bindings": {},
        "execution_contracts": [
            {
                "event_id": "event-1",
                "action_phase": "instant",
                "time_scope": "instant",
                "actor_ids": ["char-a"],
                "effort": "none",
                "timeline_ids": [],
                "knowledge_fact_ids": [],
            }
        ],
        "state_compiler": {"version": 1, "source_effect_hash": "fixture"},
    }


def _canon():
    return normalize_canon(
        {
            "gate_version": 2,
            "timeline": [],
            "entities": [
                {
                    "id": "char-a",
                    "kind": "character",
                    "name": "长篇主角",
                    "aliases": [],
                    "attributes": {},
                },
                {
                    "id": "loc-gate",
                    "kind": "location",
                    "name": "城门",
                    "aliases": [],
                    "attributes": {},
                },
            ],
            "world_rules": [],
            "milestones": [],
            "character_arcs": [],
            "initial_state": {"char-a": {"location": "loc-gate", "knowledge": []}},
        }
    )


def _brief(brief_input):
    count = brief_input["expected_beat_count"]
    target = brief_input["chapter_contract"]["target_chars"]
    each, remainder = divmod(target, count)
    return {
        "schema": BRIEF_SCHEMA,
        "chapter_contract_hash": brief_input["chapter_contract_hash"],
        "state_before_hash": brief_input["state_before_hash"],
        "input_evidence_hash": brief_input["input_evidence_hash"],
        "execution_contracts": list(
            brief_input["chapter_contract"].get("execution_contracts") or []
        ),
        "beats": [
            {
                "beat_id": f"B{index:02d}",
                "purpose": "推进发现",
                "target_chars": each + (index <= remainder),
                "allowed_entity_ids": ["char-a", "loc-gate"],
                "bound_event_ids": ["event-1"] if index == 1 else [],
                "effect_contract_ids": ["event:event-1"] if index == 1 else [],
            }
            for index in range(1, count + 1)
        ],
        "character_motivations": [{"character_id": "char-a", "motivation": "追查异常"}],
        "emotional_continuity": "保持警惕",
        "causal_bridge": "异常迫使主角追查",
        "summary": "主角发现线索",
        "cliffhanger": "线索指向城门深处",
        "setup_thread_ids": [],
        "payoff_thread_ids": [],
    }


def _blocks(count):
    passages = [
        "第一日，长篇主角发现线索。她沿城门石缝逐寸摸索，记下每次回响的间隔。",
        "雨水顺着门轴流下，守门人搬来油灯，照见铁件后方新脱落的灰屑。",
        "主角把灰屑装进纸包，又比对墙根旧痕，发现两处裂口并非同时形成。",
        "换岗钟声响过，来往脚步渐少，她趁空重新测量门洞两侧的细微高差。",
        "风从城外灌入，灯焰忽然偏斜，暗处传来的震动也随之变得更加清楚。",
        "老守卫翻出维修簿，指给她看去年雨季的记录，却没有对应这道新裂纹。",
        "主角请同伴守住门闩，自己绕到外墙检查，在泥水里找到半枚陌生印痕。",
        "天色将明，她封好纸包并写下复查次序，决定先追查印痕的真正来源。",
    ]
    return [
        {
            "block_id": f"B{index:02d}",
            "content_text": passages[index - 1] * 12,
        }
        for index in range(1, count + 1)
    ]


def test_v3_pipeline_uses_three_calls_and_ready_resume_is_model_free(
    db_session, monkeypatch
):
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
    invocation_id = 100

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
            payload = {
                "proofs": [{"contract_id": "event:event-1", "sentence_ids": ["S0001"]}],
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
    assert len(calls) == 3
    assert calls[2].startswith("audit.1.")
    entry = revision.continuity_ledger["chapters"]["1"]
    assert entry["status"] == "ready"
    assert entry["extraction_status"] == "ready"
    assert revision.continuity_ledger["prose_length_control"] == {
        "schema": "story_novel_prose_length_control.v1",
        "activated_from_position": 1,
    }
    length_control = entry["stage_metrics"]["prose"]["length_control"]
    assert length_control["source_invocation_ids"] == [102]
    assert len(length_control["initial_prose_body_hash"]) == 64
    body_hash = revision.chapters[0].content_hash
    calls.clear()
    anyio.run(generate_or_resume_chapter, service, revision, task, row, generate)
    assert calls == []
    assert revision.chapters[0].content_hash == body_hash

    entry = dict(revision.continuity_ledger["chapters"]["1"])
    entry.update(
        status="memory_ready",
        stage="memory_ready",
        extraction_status="pending",
        event_ids=[],
        memory_ids=[],
    )
    ledger = dict(revision.continuity_ledger)
    ledger["chapters"] = {"1": entry}
    revision.continuity_ledger = ledger
    db_session.commit()
    anyio.run(generate_or_resume_chapter, service, revision, task, row, generate)
    assert calls == []
    assert revision.chapters[0].content_hash == body_hash
    assert revision.continuity_ledger["chapters"]["1"]["extraction_status"] == "ready"
