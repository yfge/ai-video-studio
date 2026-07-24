import json

import pytest
from app.services.story.story_novel_canon_service import (
    CANON_GATE_VERSION,
    normalize_canon,
)
from app.services.story.story_novel_planning_phases import _canon_repair_prompt


def _problem_canon() -> dict:
    entities = [
        ("char-target", "character"),
        ("loc-start", "location"),
        ("obj-key", "object"),
        ("obj-r17", "object"),
    ]
    outcomes = [
        ("mile-1", 1, "obj-key", "owner_id", "char-target"),
        ("mile-3", 3, "obj-r17", "status", "sealed"),
        ("mile-22", 22, "obj-key", "owner_id", "char-target"),
    ]
    return {
        "gate_version": CANON_GATE_VERSION,
        "timeline": [],
        "entities": [
            {
                "id": item_id,
                "kind": kind,
                "name": item_id,
                "aliases": [],
                "attributes": {},
            }
            for item_id, kind in entities
        ],
        "world_rules": [],
        "milestones": [
            {
                "id": item_id,
                "label": item_id,
                "planned_position": position,
                "repeatable": False,
                "outcomes": [
                    {
                        "subject_id": subject_id,
                        "field": field,
                        "operator": "eq",
                        "value": value,
                    }
                ],
            }
            for item_id, position, subject_id, field, value in outcomes
        ],
        "character_arcs": [],
        "initial_state": {
            "char-target": {"location": "loc-start"},
            "obj-key": {"owner_id": None},
            "obj-r17": {"status": "sealed"},
        },
    }


def test_canon_repair_context_includes_every_failing_milestone():
    prior = _problem_canon()
    with pytest.raises(ValueError) as exc_info:
        normalize_canon(prior, required_gate_version=CANON_GATE_VERSION)
    error = str(exc_info.value)
    assert "重复 milestone outcome" in error
    assert "状态提前包含未来里程碑结果" in error

    repair = _canon_repair_prompt(
        "原始提示",
        json.dumps(prior, ensure_ascii=False),
        error,
    )

    context_text = repair.split("repair_context：", 1)[1].split(
        "\n上一次完整 Canon", 1
    )[0]
    context = json.loads(context_text)
    assert [item["id"] for item in context["failing_milestones"]] == [
        "mile-1",
        "mile-3",
        "mile-22",
    ]
    assert context["delete_milestone_ids"] == ["mile-22"]
    assert context["existing_milestone_ids"] == ["mile-1", "mile-3", "mile-22"]
    assert '"obj-r17":{"status":"sealed"}' in repair


def test_canon_repair_keeps_complete_previous_canon_and_forbids_scope_growth():
    prior = {
        "initial_state": {"obj-key": {"owner_id": "char-source"}},
        "milestones": [{"id": "mile-1", "outcomes": []}],
        "padding": "x" * 9000,
        "tail_marker": "complete-canon-tail",
    }

    repair = _canon_repair_prompt(
        "原始提示",
        json.dumps(prior, ensure_ascii=False),
        "一次性里程碑缺少 outcomes: mile-1",
    )

    assert "complete-canon-tail" in repair
    assert "禁止新增、拆分、改名或顺带重写未报错的 milestone" in repair
    assert "临时权限的取得与到期不得创建 milestone" in repair
    assert "重复 outcome 必须只保留 planned_position 最早的一条" in repair
    assert "从所有更晚 milestone 删除完全相同" in repair
    assert "outcomes 为空的 milestone 必须整条删除" in repair
    assert '"delete_milestone_ids":["mile-1"]' in repair
    assert "每个 ID 都必须从 milestones 数组整条删除" in repair
    assert "若更早 milestone 已明确把 null 改给持有人" in repair
    assert "普通归档物件删除冗余 owner_id outcome" in repair
    assert "状态提前错误若来自 entity.attributes" in repair


def test_canon_repair_lists_every_duplicate_only_milestone_for_deletion():
    def milestone(item_id, position, subject_id, field, value):
        return {
            "id": item_id,
            "planned_position": position,
            "outcomes": [
                {
                    "subject_id": subject_id,
                    "field": field,
                    "operator": "eq",
                    "value": value,
                }
            ],
        }

    prior = {
        "milestones": [
            milestone("mile-1", 1, "object-key", "owner_id", "char-liyan"),
            milestone("mile-7", 12, "char-liyan", "status", "level-one"),
            milestone("mile-15", 21, "char-liyan", "status", "level-one"),
            milestone("mile-16", 22, "object-key", "owner_id", "char-liyan"),
            milestone("mile-24", 30, "object-key", "owner_id", "char-liyan"),
            milestone("mile-25", 31, "char-liyan", "status", "level-one"),
        ]
    }
    error = (
        "重复 milestone outcome: mile-1, mile-16, mile-24；"
        "重复 milestone outcome: mile-7, mile-15, mile-25"
    )

    repair = _canon_repair_prompt(
        "原始提示", json.dumps(prior, ensure_ascii=False), error
    )
    context = json.loads(
        repair.split("repair_context：", 1)[1].split("\n上一次完整 Canon", 1)[0]
    )

    assert context["delete_milestone_ids"] == [
        "mile-15",
        "mile-16",
        "mile-24",
        "mile-25",
    ]
