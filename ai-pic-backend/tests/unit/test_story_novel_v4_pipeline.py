import json

import anyio
from app.services.story import story_novel_chapter_v4, story_novel_planning_invocations
from app.services.story.story_novel_canon_service import normalize_canon
from app.services.story.story_novel_chapter_service import generate_or_resume_chapter
from app.services.story.story_novel_incremental_plan import (
    build_chapter_skeletons,
    incremental_plan_fields,
)
from app.services.story.story_novel_length_service import generation_plan_hash
from sqlalchemy import event
from tests.unit.story_novel_v3_test_support import (
    _planning_evidence,
    persisted_stage_text,
)
from tests.unit.test_story_novel_incremental_pipeline import _blocks
from tests.unit.test_story_novel_incremental_planning import _outline_row
from tests.unit.test_story_novel_longform import _canon, _setup


def _intent(target_chars: int) -> dict:
    base, extra = divmod(target_chars, 6)
    return {
        "beats": [
            {
                "beat_id": f"B{index:02d}",
                "purpose": f"推进第 {index} 个叙事动作",
                "target_chars": base + int(index <= extra),
                "event_handles": ["E01"] if index == 1 else [],
                "character_handles": ["C01"],
            }
            for index in range(1, 7)
        ],
        "character_motivations": [
            {"character_handle": "C01", "motivation": "解决当前困难"}
        ],
        "emotional_continuity": "紧迫感延续为明确行动",
        "causal_bridge": "眼前压力迫使主角采取行动",
        "summary": "主角完成当前行动",
        "cliffhanger": "新的选择随即出现",
        "entity_proposals": [],
    }


def test_v4_pipeline_freezes_every_call_and_ready_resume_is_model_free(
    db_session, monkeypatch
):
    _user, _story, service, revision, task, *_ = _setup(db_session, with_character=True)
    canon = normalize_canon({**_canon(), "timeline": []})
    skeletons = build_chapter_skeletons(
        canon,
        {"chapters": [_outline_row(1, "主角开垦第一块薄田")]},
        [],
    )
    plan = {
        "schema": "story_novel_generation_plan.v4",
        "version": 4,
        "status": "ready",
        "phase": "ready",
        "outline_hash": "outline-v4",
        "model_policy": {
            "planning_model": "deepseek:planning",
            "prose_model": "deepseek:prose",
            "audit_model": "deepseek:audit",
        },
        "canon": canon,
        "canon_hash": canon["canon_hash"],
        "chapter_count": 1,
        "chapters": skeletons,
        "thread_payoffs": [],
    }
    plan.update(
        incremental_plan_fields(
            canon,
            skeletons,
            schema=plan["schema"],
            snapshot=revision.story_snapshot,
        )
    )
    revision.generation_plan = plan
    story_novel_planning_invocations.record_attempt(
        revision,
        "canon",
        _planning_evidence(
            revision, 500, "canon", "story_novel_canon_v3", db=db_session
        ),
        result_hash=canon["canon_hash"],
    )
    plan = dict(revision.generation_plan)
    story_novel_planning_invocations.finalize(plan, canon, skeletons)
    plan["plan_hash"] = generation_plan_hash(plan)
    revision.generation_plan = plan
    revision.chapter_count = 1
    revision.continuity_ledger = {
        "schema": "story_novel_continuity.v5",
        "state_status": "empty",
        "chapters": {
            "1": {
                "model_call_snapshots": {
                    "chapter_planning.1.format_repair": {"snapshot_hash": "old"}
                }
            }
        },
    }
    db_session.commit()
    calls, prompts = [], {}
    committed_statuses = []
    source_guards = []
    original_guard = story_novel_chapter_v4.lock_chapter_execution_source

    def guarded(*args):
        source_guards.append(args[-1]["stage"])
        return original_guard(*args)

    monkeypatch.setattr(
        story_novel_chapter_v4, "lock_chapter_execution_source", guarded
    )

    def capture_commit(_session):
        committed_statuses.append(
            ((revision.continuity_ledger or {}).get("chapters") or {})
            .get("1", {})
            .get("status")
        )

    event.listen(db_session, "after_commit", capture_commit)
    invocation_id = 500

    async def generate(_revision, prompt, *, stage, **_kwargs):
        nonlocal invocation_id
        invocation_id += 1
        calls.append(stage)
        prompts[stage] = str(prompt)
        templates = revision.generation_plan["prompt_templates"]["templates"]
        if stage.startswith("arc_planning"):
            payload, template = {
                "chapters": [
                    {
                        key: skeletons[0][key]
                        for key in (
                            "position",
                            "title",
                            "goal",
                            "key_events",
                            "character_focus",
                            "open_threads",
                            "end_state",
                        )
                    }
                ],
                "character_slots": [],
                "scope_slots": [],
            }, "story_novel_arc_plan_v4"
        elif stage.startswith("chapter_planning"):
            payload, template = _intent(2500), "story_novel_chapter_intent_v4"
        elif stage.startswith("prose"):
            payload, template = {"blocks": _blocks(6)}, "story_novel_prose_blocks_v4"
        else:
            payload, template = {
                "proofs": [
                    {
                        "contract_id": "event:event-1-1",
                        "sentence_ids": ["S0001"],
                    }
                ],
                "unexpected_claims": [],
                "future_hits": [],
                "world_rule_hits": [],
            }, "story_novel_proof_audit_v3"
        rendered = {
            **templates[template],
            "rendered_hash": f"rendered-{invocation_id}",
            "system_prompt": {
                **templates["story_novel_system_v3"],
                "rendered_hash": f"system-{invocation_id}",
            },
        }
        return persisted_stage_text(
            db_session,
            revision,
            stage,
            json.dumps(payload, ensure_ascii=False),
            invocation_id,
            rendered_template=rendered,
            prompt_text=str(prompt),
        )

    try:
        anyio.run(
            generate_or_resume_chapter,
            service,
            revision,
            task,
            skeletons[0],
            generate,
        )
    finally:
        event.remove(db_session, "after_commit", capture_commit)
    assert calls[0:3] == ["arc_planning.arc-1", "chapter_planning.1", "prose.1"]
    assert calls[3].startswith("audit.1.")
    entry = revision.continuity_ledger["chapters"]["1"]
    assert entry["status"] == "ready"
    assert (
        entry["execution_generation_plan_hash"] == revision.generation_plan["plan_hash"]
    )
    assert source_guards == ["chapter_planning", "audit"]
    assert "memory_ready" not in committed_statuses
    assert committed_statuses[-1] == "ready"
    assert all(stage in entry["model_call_snapshots"] for stage in calls)
    assert "chapter_planning.1.format_repair" not in entry["model_call_snapshots"]
    assert entry["failed_model_call_snapshots"][0]["logical_stage"] == (
        "chapter_planning.1.format_repair"
    )
    assert all(
        snapshot["execution_generation_plan_hash"]
        == entry["execution_generation_plan_hash"]
        for stage, snapshot in entry["model_call_snapshots"].items()
        if stage.startswith(("prose.", "audit.", "local_repair."))
    )
    assert "database-event-id" not in prompts["prose.1"]
    body_hash = revision.chapters[0].content_hash
    calls.clear()
    anyio.run(
        generate_or_resume_chapter,
        service,
        revision,
        task,
        revision.generation_plan["chapters"][0],
        generate,
    )
    assert calls == []
    assert revision.chapters[0].content_hash == body_hash
