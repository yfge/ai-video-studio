import json
from types import SimpleNamespace

import pytest
from app.models.task import TaskStatus
from app.schemas.story_seed import StorySeedModel
from app.services.story.story_seed_service import (
    StorySeedService,
    ensure_confirmable_seed,
)
from app.services.story.story_seed_structure_service import _parse, structure_story_seed
from fastapi import HTTPException

ENDING = (
    "九月十九日，黎雁在三方见证下只激活一次零号风钥并让它熔毁，"
    "岑野以公开身份完成合法接管，众人手动重置天衡塔阀阵。"
    "九月二十一日第一场雨抵达，六城把路线、水网和塔心权限拆分给"
    "可撤销的公共议会。"
)


def _seed(ending=ENDING):
    chapters = [
        {
            "position": position,
            "title": f"第{position}章",
            "goal": "推进冲突",
            "key_events": [f"事件{position}"],
            "character_focus": ["黎雁"],
            "open_threads": [],
            "end_state": "继续追查",
        }
        for position in range(1, 49)
    ]
    chapters[-1].update(
        {
            "title": "九月二十一日的雨",
            "goal": "在固定日期收束人物与全部硬线索。",
            "key_events": [
                "9月21日第一场雨抵达六城",
                "黎雁把熔毁风钥的残片交入公共档案并选择继续修复邮路",
            ],
            "end_state": (
                "全书结束：红尘、驼铃、星图、见证印均已回收；风钥熔毁；"
                "权限公开拆分；人物伤势进入康复而非消失。"
            ),
        }
    )
    return {
        "schema": "story_seed_v2",
        "title": "风钥",
        "premise": "黎雁守护六城",
        "outline_text": "第1章至第48章",
        "structured_outline": {
            "status": "confirmed",
            "version": 1,
            "thread_schedule_version": 1,
            "thread_payoffs": [],
            "chapters": chapters,
        },
        "protagonists": [
            {
                "virtual_ip_business_id": "vip-1",
                "initial_state": "尚未掌握风钥",
            }
        ],
        "world_constraints": [],
        "central_conflict": "权限归属",
        "ending_direction": ending,
        "content_constraints": [],
    }


def test_semantic_ending_coverage_passes_structure_and_confirmation():
    seed = _seed()
    ensure_confirmable_seed(StorySeedModel.model_validate(seed))
    parsed, error = _parse(
        json.dumps(
            {"structured_outline": seed["structured_outline"]},
            ensure_ascii=False,
        ),
        list(range(1, 49)),
        seed["ending_direction"],
    )
    assert parsed is not None
    assert error is None


def test_superficial_ending_overlap_fails_structure_and_confirmation():
    seed = _seed("主角重写规则并公开全部真相")
    last = seed["structured_outline"]["chapters"][-1]
    last["title"] = "主角进入最后一战"
    last["key_events"] = ["另一个事件"]
    last["end_state"] = "另一个结局"

    with pytest.raises(HTTPException) as exc:
        ensure_confirmable_seed(StorySeedModel.model_validate(seed))
    assert "ending_direction" in str(exc.value.detail)
    parsed, error = _parse(
        json.dumps(
            {"structured_outline": seed["structured_outline"]},
            ensure_ascii=False,
        ),
        list(range(1, 49)),
        seed["ending_direction"],
    )
    assert parsed is None
    assert "ending_direction" in (error or "")


@pytest.mark.asyncio
async def test_structure_repair_runs_when_first_result_misses_ending(monkeypatch):
    seed = _seed()
    bad = json.loads(json.dumps(seed["structured_outline"], ensure_ascii=False))
    bad["chapters"][-1].update(
        {
            "title": "主角进入最后一战",
            "key_events": ["另一个事件"],
            "end_state": "另一个结局",
        }
    )
    arcs = {
        "progression_plan": {
            "planning_structure_version": 1,
            "requested_chapter_count": 48,
            "progression_arcs": [
                _arc("arc-001", 1, 32),
                _arc("arc-002", 33, 48),
            ],
        }
    }
    outputs = iter(
        [
            json.dumps(arcs, ensure_ascii=False),
            _batch(seed["structured_outline"]["chapters"][:32]),
            _batch(bad["chapters"][32:]),
            _batch(seed["structured_outline"]["chapters"][32:]),
        ]
    )
    calls = []

    async def generate_text(*args, **kwargs):
        calls.append((args, kwargs))
        return next(outputs)

    monkeypatch.setattr(
        StorySeedService, "apply_local_update", lambda *args, **kwargs: None
    )
    story = SimpleNamespace(
        story_seed={
            **seed,
            "schema": "story_seed_v1",
            "outline": seed["outline_text"],
            "structured_outline": None,
        },
        story_seed_version=1,
    )
    task = SimpleNamespace(id=7, status=TaskStatus.PENDING, description="")
    db = SimpleNamespace(commit=lambda: None, refresh=lambda _value: None)

    upgraded = await structure_story_seed(
        db,
        story,
        task,
        SimpleNamespace(),
        generate_text,
        expected_version=1,
    )

    assert len(calls) == 4
    assert "final chapter does not cover ending_direction" in calls[-1][0][1]
    assert upgraded.schema_version == "story_seed_v2"
    assert upgraded.structured_outline.planning_structure_version == 1


def _arc(arc_id: str, start: int, end: int) -> dict:
    return {
        "arc_id": arc_id,
        "title": f"第{start}至{end}章阶段",
        "start_position": start,
        "end_position": end,
        "narrative_goal": "推进当前阶段冲突",
        "ending_state": "阶段结果形成",
        "growth": {
            "cognition": None,
            "capability": None,
            "resources": None,
            "activity_and_time_scale": None,
        },
        "major_entries": [],
        "world_scope_changes": [],
        "threads": [],
    }


def _batch(chapters: list[dict]) -> str:
    return json.dumps({"chapters": chapters, "thread_payoffs": []}, ensure_ascii=False)
