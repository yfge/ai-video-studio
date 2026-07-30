import copy
import json
from types import SimpleNamespace

import pytest
from app.schemas.story_novel_export import StoryNovelCreateRevisionRequest
from app.services.story.story_novel_ai_prompts import structured_outline_prompt
from app.services.story.story_novel_length_service import build_length_plan
from app.services.story.story_novel_thread_schedule_checkpoint import (
    reusable_thread_payoffs,
)
from app.services.story.story_seed_structure_service import _parse
from app.services.story.story_seed_thread_contract import validate_seed_thread_contract


def _outline():
    return {
        "status": "confirmed",
        "version": 2,
        "thread_schedule_version": 1,
        "chapters": [
            {
                "position": 1,
                "title": "打开",
                "goal": "提出疑问",
                "key_events": ["发现异常"],
                "character_focus": [],
                "open_threads": ["谁改写了数据"],
                "end_state": "疑问仍未解决",
            },
            {
                "position": 2,
                "title": "回答",
                "goal": "闭合疑问",
                "key_events": [
                    "关于“谁改写了数据”的最终证据确认：审计证明裴衡改写了数据"
                ],
                "character_focus": [],
                "open_threads": [],
                "end_state": "真相已公开",
            },
        ],
        "thread_payoffs": [
            {
                "thread_id": "谁改写了数据",
                "payoff_position": 2,
                "evidence_key_event": (
                    "关于“谁改写了数据”的最终证据确认：审计证明裴衡改写了数据"
                ),
            }
        ],
    }


def test_thread_contract_requires_unique_later_exact_payoff():
    outline = _outline()

    assert (
        validate_seed_thread_contract(outline, require_version=True)
        == outline["thread_payoffs"]
    )

    same_chapter = copy.deepcopy(outline)
    same_chapter["thread_payoffs"][0]["payoff_position"] = 1
    same_chapter["thread_payoffs"][0]["evidence_key_event"] = "发现异常"
    with pytest.raises(ValueError, match="必须在更晚章节回收"):
        validate_seed_thread_contract(same_chapter, require_version=True)

    paraphrased = copy.deepcopy(outline)
    paraphrased["thread_payoffs"][0]["evidence_key_event"] = "裴衡修改了数据"
    with pytest.raises(ValueError, match="未逐字复制"):
        validate_seed_thread_contract(paraphrased, require_version=True)

    neutral = copy.deepcopy(outline)
    neutral["chapters"][1]["key_events"] = ["裴衡承认自己改写了数据"]
    neutral["thread_payoffs"][0]["evidence_key_event"] = "裴衡承认自己改写了数据"
    assert validate_seed_thread_contract(neutral, require_version=True)


def test_structure_parse_requires_versioned_thread_contract():
    outline = _outline()
    parsed, error = _parse(
        json.dumps({"structured_outline": outline}, ensure_ascii=False),
        [1, 2],
    )
    assert error is None
    assert parsed is not None

    projected = copy.deepcopy(outline)
    projected["chapters"][1]["key_events"] = ["目标章原有事件"]
    parsed, error = _parse(
        json.dumps({"structured_outline": projected}, ensure_ascii=False),
        [1, 2],
    )
    assert parsed is None
    assert "evidence_key_event 未逐字复制" in error

    neutral = copy.deepcopy(outline)
    neutral_event = "裴衡承认自己改写了数据"
    neutral["chapters"][1]["key_events"] = [neutral_event]
    neutral["thread_payoffs"][0]["evidence_key_event"] = neutral_event
    parsed, error = _parse(
        json.dumps({"structured_outline": neutral}, ensure_ascii=False),
        [1, 2],
    )
    assert error is None
    assert parsed.thread_payoffs[0].evidence_key_event == neutral_event
    assert parsed.chapters[1].key_events == [neutral_event]

    duplicated = copy.deepcopy(outline)
    duplicated["chapters"][0]["key_events"].append(
        duplicated["thread_payoffs"][0]["evidence_key_event"]
    )
    with pytest.raises(ValueError, match="必须全书唯一"):
        validate_seed_thread_contract(duplicated, require_version=True)

    legacy = copy.deepcopy(outline)
    legacy["thread_schedule_version"] = 0
    legacy["thread_payoffs"] = []
    parsed, error = _parse(
        json.dumps({"structured_outline": legacy}, ensure_ascii=False),
        [1, 2],
    )
    assert parsed is None
    assert "thread_schedule_version=1" in error


def test_length_plan_checkpoints_confirmed_seed_thread_payoffs():
    outline = _outline()
    story = SimpleNamespace(
        story_seed={
            "schema": "story_seed_v2",
            "structured_outline": outline,
        },
        story_seed_status="confirmed",
        story_seed_version=7,
    )

    plan = build_length_plan(story, StoryNovelCreateRevisionRequest())

    assert plan["thread_payoffs"] == outline["thread_payoffs"]
    assert plan["thread_payoffs_hash"]
    assert plan["thread_payoffs_outline_hash"] == plan["outline_hash"]
    assert reusable_thread_payoffs(plan) == outline["thread_payoffs"]


def test_thread_contract_rejects_missing_and_overloaded_payoffs():
    outline = _outline()
    outline["chapters"][0]["open_threads"] = [
        "thread-a",
        "thread-b",
        "thread-c",
        "thread-d",
    ]
    outline["thread_payoffs"] = [
        {
            "thread_id": thread_id,
            "payoff_position": 2,
            "evidence_key_event": f"关于“{thread_id}”的最终证据确认：审计证明其来源",
        }
        for thread_id in outline["chapters"][0]["open_threads"]
    ]
    outline["chapters"][1]["key_events"] = [
        row["evidence_key_event"] for row in outline["thread_payoffs"]
    ]

    with pytest.raises(ValueError, match="超过单章上限 3"):
        validate_seed_thread_contract(outline, require_version=True)

    outline["thread_payoffs"].pop()
    with pytest.raises(ValueError, match="伏笔回收合同遗漏"):
        validate_seed_thread_contract(outline, require_version=True)


def test_thread_contract_rejects_compound_thread_ids():
    outline = _outline()
    outline["chapters"][0]["open_threads"] = ["观测员下落；云井审计编号"]
    outline["thread_payoffs"][0]["thread_id"] = "观测员下落；云井审计编号"

    with pytest.raises(ValueError, match="只表达一个原子问题"):
        validate_seed_thread_contract(outline, require_version=True)


def test_structure_prompt_forbids_carrying_open_thread_ids_forward():
    prompt = structured_outline_prompt(story_seed={}, expected_positions=[1, 2])

    assert "同一 ID 在全书只能" in prompt
    assert "后续章节不得重复携带" in prompt
