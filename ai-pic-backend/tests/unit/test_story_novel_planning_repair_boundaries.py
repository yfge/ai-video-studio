import json

import anyio
import pytest
from app.services.story.story_novel_canon_service import validate_generation_plan
from app.services.story.story_novel_planning_phases import _canon_repair_prompt
from app.services.story.story_novel_planning_service import ensure_generation_plan
from tests.unit.test_story_novel_longform import _canon, _plan_row, _setup


def test_canon_format_repair_preserves_clean_initial_state():
    prior = {
        "initial_state": {
            "obj-key": {"owner_id": "char-source"},
            "char-target": {"possessions": []},
        },
        "milestones": [
            {
                "id": "mile-43",
                "outcomes": [
                    {
                        "subject_id": "obj-seal",
                        "field": "owner_id",
                        "operator": "eq",
                        "value": "null",
                    }
                ],
            }
        ],
    }

    repair = _canon_repair_prompt(
        "原始提示",
        json.dumps(prior, ensure_ascii=False),
        "里程碑 outcome value 必须使用真实 JSON 值: mile-43",
    )

    assert '"owner_id":"char-source"' in repair
    assert '"failing_milestones":[{"id":"mile-43"' in repair
    assert "必须逐字段原样复制该干净初态" in repair


def test_canon_repair_does_not_lock_an_invalid_initial_state():
    prior = {
        "initial_state": {"obj-key": {"location": "unknown-location"}},
        "milestones": [],
    }

    repair = _canon_repair_prompt(
        "原始提示",
        json.dumps(prior, ensure_ascii=False),
        "初始状态引用未知地点: ['unknown-location']",
    )

    assert '"preserve_initial_state_exactly":null' in repair


def test_canon_repair_includes_every_failing_milestone():
    prior = {
        "initial_state": {
            "zero-wind-key": {"owner_id": "li-yan"},
            "li-yan": {"permissions": ["zero-level"]},
        },
        "milestones": [
            {"id": item_id, "outcomes": []}
            for item_id in ("mile-1", "mile-3", "mile-22", "mile-30")
        ],
    }
    error = (
        "重复 milestone outcome: mile-1, mile-22, mile-30；"
        "状态提前包含未来里程碑结果: 第 3 章 mile-3 li-yan.permissions"
    )

    repair = _canon_repair_prompt(
        "原始提示",
        json.dumps(prior, ensure_ascii=False),
        error,
    )

    for item_id in ("mile-1", "mile-3", "mile-22", "mile-30"):
        assert f'"id":"{item_id}"' in repair
    assert '"preserve_initial_state_exactly":null' in repair


def test_outline_plan_has_no_application_chapter_cap(db_session):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    rows = [_plan_row(position) for position in range(1, 26)]
    calls = []

    async def generate(*_args, **kwargs):
        calls.append(kwargs["max_tokens"])
        payload = _canon() if len(calls) == 1 else {"chapters": rows}
        return json.dumps(payload, ensure_ascii=False)

    plan = anyio.run(ensure_generation_plan, service, revision, task, generate)
    assert plan["chapter_count"] == 25
    assert revision.chapter_count == 25
    assert revision.target_words == 75000
    assert plan["schema"] == "story_novel_generation_plan.v2"
    assert len(plan["canon_hash"]) == 64
    assert calls == [16000, 16000]


def test_plan_rejects_terminal_payoff_dump():
    canon = _canon()
    rows = [_plan_row(position) for position in range(1, 6)]
    for position, row in enumerate(rows[:-1], start=1):
        row["open_threads"] = [f"thread-{position}"]
    rows[-1]["key_events"] = ["一次性回收所有线索"]
    rows[-1]["payoffs_due"] = [f"thread-{position}" for position in range(1, 5)]

    with pytest.raises(ValueError, match="集中回收 4 条伏笔"):
        validate_generation_plan(canon, rows)
