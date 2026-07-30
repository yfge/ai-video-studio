import json
from types import SimpleNamespace

import anyio
from app.services.story.story_novel_outline_merge import merge_frozen_chapters
from app.services.story.story_novel_plan_repair import (
    _repair_context,
    plan_repair_prompt,
)
from app.services.story.story_novel_planning_service import ensure_generation_plan
from app.services.story.story_novel_thread_schedule import compile_thread_payoffs
from tests.unit.test_story_novel_longform import _canon, _plan_row, _setup


def _frozen_one_thread():
    rows = [_plan_row(1), _plan_row(2)]
    rows[0]["open_threads"] = ["thread-stable"]
    rows[1]["key_events"] = ["揭开稳定伏笔"]
    return {
        "schema": "story_novel_generation_plan.v2",
        "version": 4,
        "status": "ready",
        "phase": "spec_ready",
        "outline_hash": "outline-hash",
        "chapters": rows,
    }


def test_real_planning_call_sequence_schedules_threads_before_full_plan(db_session):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    revision.generation_plan = _frozen_one_thread()
    db_session.commit()
    calls = []

    async def generate(_revision, prompt, *, max_tokens):
        calls.append((prompt, max_tokens))
        if "编译唯一 Canon" in prompt:
            return json.dumps(_canon(), ensure_ascii=False)
        if "只依据冻结 structured_outline" in prompt:
            assert task.description == "Canon 编译完成，正在规划伏笔回收…"
            assert "允许共享同一个 exact evidence_key_event" in prompt
            assert '"title":"第2章"' in prompt
            assert '"goal":"推进核心冲突"' in prompt
            assert '"end_state":"主角决定追查"' in prompt
            return json.dumps(
                {
                    "thread_payoffs": [
                        {
                            "thread_id": "thread-stable",
                            "payoff_position": 2,
                            "evidence_key_event": "揭开稳定伏笔",
                        }
                    ]
                },
                ensure_ascii=False,
            )
        assert task.description == "伏笔调度完成，正在规划章节合同…"
        assert "机器校验后的 thread_payoffs 是唯一权威" in prompt
        assert '"thread_id":"thread-stable"' in prompt
        generated = [_plan_row(1), _plan_row(2)]
        generated[1]["key_events"] = ["揭开稳定伏笔"]
        generated[0]["open_threads"] = ["machine-invented"]
        generated[1]["payoffs_due"] = ["machine-invented"]
        return json.dumps({"chapters": generated}, ensure_ascii=False)

    plan = anyio.run(ensure_generation_plan, service, revision, task, generate)

    assert len(calls) == 3
    assert [value for _, value in calls] == [16000, 16000, 16000]
    assert "只依据冻结 structured_outline" in calls[1][0]
    assert "规划一部长篇小说" in calls[2][0]
    assert plan["chapters"][0]["open_threads"] == ["thread-stable"]
    assert plan["chapters"][1]["payoffs_due"] == ["thread-stable"]
    assert plan["thread_payoffs"][0]["thread_id"] == "thread-stable"
    assert plan["thread_payoffs_hash"]
    assert plan["thread_payoffs_outline_hash"] == "outline-hash"
    assert task.description == "规划完成，共 2 章"


def test_invalid_schedule_gets_exactly_one_provider_repair():
    frozen = _frozen_one_thread()
    calls = []
    revision = SimpleNamespace(generation_plan={})

    class Task:
        status = "pending"

    async def generate(_revision, prompt, *, max_tokens):
        calls.append((prompt, max_tokens))
        if len(calls) == 1:
            return '{"thread_payoffs":[]}'
        return json.dumps(
            {
                "thread_payoff_repairs": [
                    {
                        "thread_id": "thread-stable",
                        "payoff_position": 2,
                        "evidence_key_event": "揭开稳定伏笔",
                    }
                ]
            },
            ensure_ascii=False,
        )

    result = anyio.run(
        compile_thread_payoffs,
        SimpleNamespace(),
        Task(),
        generate,
        revision,
        frozen,
    )

    assert result[0]["thread_id"] == "thread-stable"
    assert len(calls) == 2
    assert "只允许提交一次最小修复" in calls[1][0]
    assert "authoritative_conflict_thread_ids" in calls[1][0]
    assert [value for _, value in calls] == [16000, 16000]
    entries = revision.generation_plan["planning_invocations"]["entries"]
    assert [item["logical_stage"] for item in entries] == [
        "thread_schedule.initial",
        "thread_schedule.repair",
    ]
    assert entries[0]["result_hash"] == entries[1]["result_hash"]


def test_merge_ignores_machine_payoffs_when_schedule_is_authoritative():
    generated = [_plan_row(1), _plan_row(2)]
    generated[1]["key_events"] = ["揭开稳定伏笔"]
    generated[0]["open_threads"] = ["machine-thread"]
    generated[1]["payoffs_due"] = ["machine-thread"]
    frozen = _frozen_one_thread()
    schedule = [
        {
            "thread_id": "thread-stable",
            "payoff_position": 2,
            "evidence_key_event": "揭开稳定伏笔",
        }
    ]

    merged = merge_frozen_chapters(generated, frozen, _canon(), schedule)

    assert merged[0]["open_threads"] == ["thread-stable"]
    assert merged[1]["payoffs_due"] == ["thread-stable"]


def test_plan_repair_context_exposes_exactly_undefined_initial_fields():
    canon = {
        "entities": [
            {
                "id": "loc-cargo-train",
                "kind": "location",
                "name": "货运列车",
                "aliases": [],
                "attributes": {},
            }
        ],
        "initial_state": {
            "loc-cargo-train": {"location": "loc-cargo-train"},
        },
    }
    context = _repair_context(
        "{}", "loc-cargo-train.status 起点不连续", canon, {}, None
    )

    assert context["authoritative_initial_state"] == {
        "loc-cargo-train": {"location": "loc-cargo-train"}
    }
    assert "status" not in context["authoritative_initial_state"]["loc-cargo-train"]
    repair = plan_repair_prompt(
        "原始提示",
        "{}",
        "loc-cargo-train.status 起点不连续",
        [1],
        canon=canon,
    )
    assert "其中未出现的 subject/field 就是未定义" in repair
    assert '"loc-cargo-train":{"location":"loc-cargo-train"}' in repair
