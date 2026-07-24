import json

import anyio
import pytest
from app.services.story.story_novel_task_guard import NovelTaskCancelled
from app.services.story.story_novel_thread_schedule import (
    compile_thread_payoffs,
    parse_thread_payoffs,
    thread_schedule_repair_prompt,
)
from tests.unit.test_story_novel_longform import _plan_row


def test_schedule_reports_all_semantic_conflicts_in_one_diagnostic():
    contract = [
        {
            "position": 1,
            "open_threads": [
                "thread-a",
                "thread-b",
                "thread-c",
                "thread-d",
                "thread-e",
                "thread-missing",
            ],
            "key_events": ["打开线索"],
        },
        {
            "position": 2,
            "open_threads": [],
            "key_events": ["解决线索"],
        },
    ]
    rows = [
        {
            "thread_id": "thread-a",
            "payoff_position": 1,
            "evidence_key_event": "打开线索",
        },
        {
            "thread_id": "thread-a",
            "payoff_position": 2,
            "evidence_key_event": "解决线索",
        },
        {
            "thread_id": "thread-unknown",
            "payoff_position": 2,
            "evidence_key_event": "解决线索",
        },
        {
            "thread_id": "thread-b",
            "payoff_position": 2,
            "evidence_key_event": "近义改写",
        },
        {
            "thread_id": "thread-c",
            "payoff_position": 2,
            "evidence_key_event": "解决线索",
        },
        {
            "thread_id": "thread-d",
            "payoff_position": 2,
            "evidence_key_event": "解决线索",
        },
        {
            "thread_id": "thread-e",
            "payoff_position": 99,
            "evidence_key_event": "解决线索",
        },
    ]
    parsed, error = parse_thread_payoffs(
        json.dumps({"thread_payoffs": rows}, ensure_ascii=False), contract
    )

    assert parsed is None
    for message in (
        "提前回收: thread-a",
        "重复回收: thread-a",
        "未知伏笔: thread-unknown",
        "payoff_position 无效: 99",
        "evidence_key_event 未逐字复制",
        "伏笔调度遗漏: ['thread-missing']",
        "第 2 章集中回收 5 条伏笔",
    ):
        assert message in error


def test_three_related_threads_may_share_one_exact_key_event():
    contract = [
        {
            "position": 1,
            "open_threads": ["thread-a", "thread-b", "thread-c"],
            "key_events": ["打开三条相关线索"],
        },
        {"position": 2, "open_threads": [], "key_events": ["同一供词回答三条线索"]},
    ]
    rows = [
        {
            "thread_id": thread_id,
            "payoff_position": 2,
            "evidence_key_event": "同一供词回答三条线索",
        }
        for thread_id in ("thread-a", "thread-b", "thread-c")
    ]

    parsed, error = parse_thread_payoffs(json.dumps({"thread_payoffs": rows}), contract)

    assert error is None
    assert parsed == rows


def test_four_shared_evidence_payoffs_still_exceed_chapter_limit():
    contract = [
        {
            "position": 1,
            "open_threads": [f"thread-{index}" for index in range(4)],
            "key_events": ["打开四条线索"],
        },
        {"position": 2, "open_threads": [], "key_events": ["同一事件回答全部线索"]},
    ]
    rows = [
        {
            "thread_id": f"thread-{index}",
            "payoff_position": 2,
            "evidence_key_event": "同一事件回答全部线索",
        }
        for index in range(4)
    ]

    parsed, error = parse_thread_payoffs(json.dumps({"thread_payoffs": rows}), contract)

    assert parsed is None
    assert "第 2 章集中回收 4 条伏笔，超过单章上限 3" in error


def test_repair_prompt_requests_only_exact_conflict_ids():
    prompt = thread_schedule_repair_prompt(
        "全部冲突", ["thread-a", "thread-b"], _repair_contract(), []
    )

    assert "只允许提交一次最小修复" in prompt
    assert "未点名行由系统原样保留" in prompt
    assert '"authoritative_conflict_thread_ids":["thread-a","thread-b"]' in prompt
    assert '"thread_id":"thread-a"' in prompt
    assert '"thread_id":"thread-b"' in prompt


def _repair_contract():
    return [
        {
            "position": 1,
            "title": "打开",
            "open_threads": ["thread-a", "thread-b"],
            "key_events": ["打开线索"],
        },
        {
            "position": 2,
            "title": "回答",
            "open_threads": [],
            "key_events": ["回答线索"],
        },
    ]


def test_schedule_budget_scales_beyond_8192_without_application_cap():
    threads = [f"thread-{index}" for index in range(60)]
    chapters = [
        {
            "position": position,
            "open_threads": threads if position == 1 else [],
            "key_events": (
                ["打开全部线索"]
                if position == 1
                else [f"事件-{position}-{slot}" for slot in range(3)]
            ),
        }
        for position in range(1, 22)
    ]
    schedule = [
        {
            "thread_id": thread_id,
            "payoff_position": 2 + index // 3,
            "evidence_key_event": f"事件-{2 + index // 3}-{index % 3}",
        }
        for index, thread_id in enumerate(threads)
    ]
    calls = []

    class Task:
        status = "pending"

    async def generate(_revision, _prompt, *, max_tokens):
        calls.append(max_tokens)
        return json.dumps({"thread_payoffs": schedule})

    result = anyio.run(
        compile_thread_payoffs,
        object(),
        Task(),
        generate,
        object(),
        {"chapters": chapters},
    )

    assert len(result) == 60
    assert calls == [18000]


def test_no_frozen_spec_or_threads_skips_schedule_provider():
    class Task:
        status = "pending"

    async def reject(*_args, **_kwargs):
        raise AssertionError("provider must not be called")

    assert (
        anyio.run(
            compile_thread_payoffs,
            object(),
            Task(),
            reject,
            object(),
            None,
        )
        is None
    )
    frozen = {"chapters": [_plan_row(1)]}
    assert (
        anyio.run(
            compile_thread_payoffs,
            object(),
            Task(),
            reject,
            object(),
            frozen,
        )
        == []
    )


def test_schedule_discards_provider_result_after_cancellation():
    rows = [_plan_row(1), _plan_row(2)]
    rows[0]["open_threads"] = ["thread-stable"]
    rows[1]["key_events"] = ["揭开稳定伏笔"]

    class Task:
        status = "pending"

    task = Task()
    calls = []

    async def generate(_revision, _prompt, *, max_tokens):
        calls.append(max_tokens)
        task.status = "cancelled"
        return '{"thread_payoffs":[]}'

    with pytest.raises(NovelTaskCancelled):
        anyio.run(
            compile_thread_payoffs,
            object(),
            task,
            generate,
            object(),
            {"chapters": rows},
        )
    assert calls == [16000]
