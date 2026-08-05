import json

import anyio
from app.services.story import story_novel_planning_invocations
from app.services.story.story_novel_brief_policy import expected_beat_count
from app.services.story.story_novel_canon_milestone_filter import (
    CANON_MODEL_FILTER_VERSION,
)
from app.services.story.story_novel_canon_service import (
    CANON_GATE_VERSION,
    normalize_canon,
)
from app.services.story.story_novel_chapter_package import (
    generate_and_checkpoint_package,
)
from app.services.story.story_novel_incremental_plan import (
    build_chapter_skeletons,
    incremental_plan_fields,
    valid_incremental_plan,
)
from app.services.story.story_novel_invocation_evidence import GeneratedNovelText
from app.services.story.story_novel_length_service import generation_plan_hash
from app.services.story.story_novel_plan_checkpoint import reusable_generation_plan
from app.services.story.story_novel_planning_service import ensure_generation_plan
from tests.unit.test_story_novel_longform import _canon, _setup


def _outline_row(position: int, event: str) -> dict:
    return {
        "position": position,
        "title": f"第{position}章",
        "goal": f"推进第{position}步",
        "key_events": [event],
        "character_focus": ["主角"],
        "open_threads": [],
        "end_state": f"完成第{position}步",
        "min_chars": 2000,
        "target_chars": 2500,
        "max_chars": 3000,
        "length_source": "profile_default",
        "length": {
            "min_chars": 2000,
            "target_chars": 2500,
            "max_chars": 3000,
            "source": "profile_default",
        },
    }


def _package(skeleton: dict) -> dict:
    count = expected_beat_count(int(skeleton["target_chars"]))
    base, extra = divmod(int(skeleton["target_chars"]), count)
    return {
        "chapter_contract": {
            **skeleton,
            "preconditions": [],
            "state_transitions": [],
            "knowledge_grants": [],
            "location_transitions": [],
            "execution_contracts": [
                {
                    "event_id": skeleton["required_event_ids"][0],
                    "action_phase": "instant",
                    "time_scope": "same_day",
                    "actor_ids": ["char-a"],
                    "effort": "light",
                    "timeline_ids": [],
                    "knowledge_fact_ids": [],
                }
            ],
        },
        "chapter_brief": {
            "beats": [
                {
                    "beat_id": f"B{index:02d}",
                    "purpose": f"推进当前章第{index}拍",
                    "target_chars": base + int(index <= extra),
                    "bound_event_ids": (
                        skeleton["required_event_ids"] if index == 1 else []
                    ),
                }
                for index in range(1, count + 1)
            ],
            "character_motivations": [
                {"character_id": "char-a", "motivation": "解决当前困难"}
            ],
            "emotional_continuity": "保持紧迫感",
            "causal_bridge": "前一结果迫使主角继续行动",
            "summary": "主角完成当前章行动",
            "cliffhanger": "新的现实压力出现",
        },
    }


def _attempt(plan: dict, template: str, invocation_id: int) -> dict:
    frozen = plan["prompt_templates"]["templates"]
    return {
        "invocation_id": invocation_id,
        "provider": "codex",
        "model": "gpt-5.6-sol",
        "status": "succeeded",
        "input_tokens": 100,
        "cache_tokens": 0,
        "output_tokens": 200,
        "finish_reason": "stop",
        "latency_ms": 10,
        "response_hash": f"response-{invocation_id}",
        "raw_response_hash": f"raw-{invocation_id}",
        "prompt_template": {
            **frozen[template],
            "rendered_hash": f"rendered-{invocation_id}",
            "system_prompt": {
                **frozen["story_novel_system_v3"],
                "rendered_hash": f"system-rendered-{invocation_id}",
            },
        },
    }


def test_v3_generation_plan_freezes_skeleton_before_any_chapter_contract(db_session):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    rows = [_outline_row(position, f"当前事件{position}") for position in range(1, 49)]
    snapshot = dict(revision.story_snapshot)
    snapshot["story_seed"] = {
        "schema": "story_seed_v2",
        "structured_outline": {"status": "frozen", "chapters": rows},
    }
    revision.story_snapshot = snapshot
    revision.generation_plan = {
        "schema": "story_novel_generation_plan.v3",
        "version": 4,
        "status": "ready",
        "phase": "spec_ready",
        "outline_hash": "outline-48",
        "model_policy": {
            "planning_model": "codex:gpt-5.6-sol",
            "prose_model": "codex:gpt-5.6-sol",
            "audit_model": "codex:gpt-5.6-sol",
        },
        "chapters": rows,
    }
    db_session.commit()
    prompts = []

    async def generate(_revision, prompt, **_kwargs):
        prompts.append(str(prompt))
        return json.dumps(_canon(), ensure_ascii=False)

    plan = anyio.run(ensure_generation_plan, service, revision, task, generate)

    assert len(prompts) == 1
    assert "编译唯一 Canon" in prompts[0]
    assert plan["chapter_contract_mode"] == "just_in_time"
    assert plan["brief_policy_version"].endswith(".v4")
    assert plan["planning_contract_version"] == 9
    assert plan["prose_execution_boundary_version"] == 1
    assert plan["prompt_templates"]["schema"] == "story_novel_prompt_policy.v10"
    assert plan["world_reveal_index"]["schema"] == ("story_novel_world_reveal_index.v1")
    assert plan["compiled_chapter_count"] == 0
    assert len(plan["chapters"]) == 48
    assert all(row["contract_status"] == "pending" for row in plan["chapters"])
    assert all(not row["execution_contracts"] for row in plan["chapters"])


def test_chapter_package_contains_current_outline_only_and_checkpoints_prefix(
    db_session,
):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    canon = normalize_canon({**_canon(), "timeline": []})
    rows = [
        _outline_row(1, "主角开垦第一块薄田"),
        _outline_row(2, "未来才发现灵泉秘密"),
    ]
    skeletons = build_chapter_skeletons(canon, {"chapters": rows}, [])
    plan = {
        "schema": "story_novel_generation_plan.v3",
        "version": 4,
        "status": "ready",
        "phase": "ready",
        "outline_hash": "outline-two",
        "model_policy": {
            "planning_model": "codex:gpt-5.6-sol",
            "prose_model": "codex:gpt-5.6-sol",
            "audit_model": "codex:gpt-5.6-sol",
        },
        "canon": canon,
        "canon_hash": canon["canon_hash"],
        "canon_gate_version": CANON_GATE_VERSION,
        "canon_model_filter_version": CANON_MODEL_FILTER_VERSION,
        "chapter_count": 2,
        "chapters": skeletons,
        "thread_payoffs": [],
    }
    plan.update(incremental_plan_fields(canon, skeletons))
    revision.generation_plan = plan
    story_novel_planning_invocations.record_attempt(
        revision,
        "canon",
        _attempt(plan, "story_novel_canon_v3", 401),
        result_hash=canon["canon_hash"],
    )
    plan = dict(revision.generation_plan)
    story_novel_planning_invocations.finalize(plan, canon, skeletons)
    plan["plan_hash"] = generation_plan_hash(plan)
    revision.generation_plan = plan
    revision.chapter_count = 2
    db_session.commit()
    prompts = []

    async def generate(_revision, prompt, **_kwargs):
        prompts.append(str(prompt))
        return GeneratedNovelText(
            json.dumps(_package(skeletons[0]), ensure_ascii=False),
            _attempt(plan, "story_novel_chapter_package_v3", 402),
        )

    contract, brief, _context, entry = anyio.run(
        generate_and_checkpoint_package,
        service,
        revision,
        1,
        skeletons[0],
        {},
        generate,
    )

    assert len(prompts) == 1
    assert "主角开垦第一块薄田" in prompts[0]
    assert "未来才发现灵泉秘密" not in prompts[0]
    assert "future_guard_index" not in prompts[0]
    assert contract["contract_status"] == "compiled"
    assert contract["state_compiler"]["version"] == 1
    assert brief["beats"][0]["effect_contract_ids"] == ["event:event-1-1"]
    assert entry["status"] == "chapter_planning"
    assert revision.generation_plan["compiled_chapter_count"] == 1
    assert revision.generation_plan["chapters"][1]["contract_status"] == "pending"
    assert valid_incremental_plan(revision.generation_plan)
    assert reusable_generation_plan(revision.generation_plan, revision.generation_plan)
