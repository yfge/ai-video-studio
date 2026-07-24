import json
from types import SimpleNamespace

import pytest
from app.schemas.story_seed import StorySeedStructuredOutline
from app.services.story.story_seed_service import StorySeedService
from app.services.story.story_seed_structure_service import structure_story_seed
from fastapi import HTTPException


def _outline():
    thread_ids = [f"thread-{index}" for index in range(5)]
    return StorySeedStructuredOutline.model_validate(
        {
            "status": "draft",
            "version": 1,
            "thread_schedule_version": 1,
            "chapters": [
                {
                    "position": 1,
                    "title": "打开",
                    "goal": "提出问题",
                    "key_events": ["发现五条异常记录"],
                    "character_focus": [],
                    "open_threads": thread_ids,
                    "end_state": "问题待查",
                },
                {
                    "position": 2,
                    "title": "首次核验",
                    "goal": "回答部分问题",
                    "key_events": [
                        f"关于“{thread_id}”的最终证据确认：回答 {thread_id}"
                        for thread_id in thread_ids
                    ],
                    "character_focus": [],
                    "open_threads": [],
                    "end_state": "仍有记录待查",
                },
                {
                    "position": 3,
                    "title": "补充核验",
                    "goal": "回答剩余问题",
                    "key_events": ["既有后续事件"],
                    "character_focus": [],
                    "open_threads": [],
                    "end_state": "全部问题闭合",
                },
            ],
            "thread_payoffs": [
                {
                    "thread_id": thread_id,
                    "payoff_position": 2,
                    "evidence_key_event": (
                        f"关于“{thread_id}”的最终证据确认：回答 {thread_id}"
                    ),
                }
                for thread_id in thread_ids
            ],
        }
    )


def _repair(rows):
    return json.dumps({"thread_payoff_repairs": rows}, ensure_ascii=False)


def _service_inputs():
    story = SimpleNamespace(
        story_seed={
            "schema": "story_seed_v1",
            "title": "档案回声",
            "premise": "审计员追查五条异常记录",
            "outline": "连续第1章至第3章",
            "protagonists": [
                {
                    "virtual_ip_business_id": "vip-1",
                    "initial_state": "刚接手审计任务",
                }
            ],
            "world_constraints": [],
            "central_conflict": "记录被系统性改写",
            "content_constraints": [],
        },
        story_seed_version=1,
    )
    task = SimpleNamespace(id=7, status="pending", description="")
    db = SimpleNamespace(commit=lambda: None, refresh=lambda _value: None)
    return db, story, task


def _valid_repair():
    return _repair(
        [
            {
                "thread_id": "thread-3",
                "payoff_position": 3,
                "evidence_key_event": "关于“thread-3”的最终证据确认：回答 thread-3",
            },
            {
                "thread_id": "thread-4",
                "payoff_position": 3,
                "evidence_key_event": "关于“thread-4”的最终证据确认：回答 thread-4",
            },
        ]
    )


@pytest.mark.asyncio
async def test_structure_uses_at_most_one_targeted_provider_repair(monkeypatch):
    outline = _outline()
    model_output = outline.model_dump()
    for row in model_output["thread_payoffs"]:
        row["evidence_key_event"] = f"回答 {row['thread_id']}"
    model_output["chapters"][1]["key_events"] = [
        row["evidence_key_event"] for row in model_output["thread_payoffs"]
    ]
    outputs = iter(
        [
            json.dumps({"structured_outline": model_output}, ensure_ascii=False),
            _valid_repair(),
        ]
    )
    calls = []
    story_marker = "不得泄露旧结构草稿"

    async def generate_text(*args, **kwargs):
        calls.append((args, kwargs))
        return next(outputs)

    writes = []
    monkeypatch.setattr(
        StorySeedService,
        "apply_local_update",
        lambda *args, **kwargs: writes.append((args, kwargs)),
    )
    db, story, task = _service_inputs()
    story.story_seed["structured_outline"] = {"marker": story_marker}

    upgraded = await structure_story_seed(
        db,
        story,
        task,
        SimpleNamespace(),
        generate_text,
        expected_version=1,
    )

    assert len(calls) == 2
    assert story_marker not in calls[0][0][1]
    assert "只允许返回一次最小伏笔补丁" in calls[1][0][1]
    assert "关于“thread-3”的最终证据确认：回答 thread-3" in calls[1][0][1]
    assert len(writes) == 1
    assert upgraded.structured_outline.thread_payoffs[-1].payoff_position == 3


@pytest.mark.asyncio
async def test_failed_targeted_repair_does_not_write_story_seed(monkeypatch):
    outline = _outline()
    outputs = iter(
        [
            json.dumps(
                {"structured_outline": outline.model_dump()}, ensure_ascii=False
            ),
            _repair(
                [
                    {
                        "thread_id": "thread-3",
                        "payoff_position": 3,
                        "evidence_key_event": "只修复一条",
                    }
                ]
            ),
        ]
    )
    calls = []

    async def generate_text(*args, **kwargs):
        calls.append((args, kwargs))
        return next(outputs)

    writes = []
    monkeypatch.setattr(
        StorySeedService,
        "apply_local_update",
        lambda *args, **kwargs: writes.append((args, kwargs)),
    )
    db, story, task = _service_inputs()

    with pytest.raises(HTTPException, match="结构化大纲无效"):
        await structure_story_seed(
            db,
            story,
            task,
            SimpleNamespace(),
            generate_text,
            expected_version=1,
        )

    assert len(calls) == 2
    assert writes == []
