import pytest
from app.services.story.story_novel_canon_service import (
    normalize_canon,
    validate_generation_plan,
)
from tests.unit.test_story_novel_longform import _canon, _plan_row


def test_plan_diagnostic_aggregates_errors_in_three_chapters():
    canon_raw = _canon()
    canon_raw["entities"].append(
        {
            "id": "loc-yard",
            "kind": "location",
            "name": "外院",
            "aliases": [],
            "attributes": {},
        }
    )
    canon = normalize_canon(canon_raw)
    rows = [_plan_row(position) for position in range(1, 4)]
    rows[0]["knowledge_grants"] = [
        {
            "character_id": "char-a",
            "fact_id": "fact-without-source",
            "source_event_id": "event-never-declared",
        }
    ]
    rows[1]["location_transitions"] = [
        {
            "subject_id": "char-a",
            "from_location_id": "loc-yard",
            "to_location_id": "loc-gate",
            "means": "步行",
        }
    ]
    rows[2]["preconditions"] = [
        {
            "subject_id": "char-a",
            "field": "status",
            "operator": "eq",
            "value": "松懈",
        }
    ]
    rows[2]["state_transitions"] = [
        {
            "subject_id": "char-a",
            "field": "status",
            "from_value": "松懈",
            "to_value": "决断",
            "reason": "同字段错误起点",
        }
    ]

    with pytest.raises(ValueError) as exc_info:
        validate_generation_plan(canon, rows)

    message = str(exc_info.value)
    assert "章节计划确定性诊断失败" in message
    assert "第 1 章知识早于事件" in message
    assert "source_event_id=event-never-declared" in message
    assert "第 2 章地点起点不连续" in message
    assert "第 3 章前置状态不连续" in message
    assert "第 3 章状态起点不连续" in message


def test_plan_diagnostic_bounds_issue_count_and_marks_truncation():
    canon = normalize_canon(_canon())
    rows = [_plan_row(position) for position in range(1, 55)]
    for row in rows:
        row["preconditions"] = [
            {
                "subject_id": "char-a",
                "field": "status",
                "operator": "eq",
                "value": f"错误状态-{row['position']}",
            }
        ]

    with pytest.raises(ValueError) as exc_info:
        validate_generation_plan(canon, rows)

    message = str(exc_info.value)
    assert len(message) <= 12000
    assert "诊断已截断" in message


def test_plan_diagnostic_reports_state_and_payoff_capacity_together():
    canon = normalize_canon(_canon())
    rows = [_plan_row(1), _plan_row(2)]
    rows[0]["open_threads"] = ["thread-a", "thread-b", "thread-c", "thread-d"]
    rows[0]["preconditions"] = [
        {
            "subject_id": "char-a",
            "field": "status",
            "operator": "eq",
            "value": "错误状态",
        }
    ]
    rows[1]["payoffs_due"] = ["thread-a", "thread-b", "thread-c", "thread-d"]

    with pytest.raises(ValueError) as exc_info:
        validate_generation_plan(canon, rows)

    message = str(exc_info.value)
    assert "前置状态不连续" in message
    assert "集中回收 4 条伏笔" in message


def test_plan_allows_three_related_payoffs_on_one_key_event():
    canon = normalize_canon(_canon())
    rows = [_plan_row(1), _plan_row(2)]
    rows[0]["open_threads"] = ["thread-a", "thread-b", "thread-c"]
    rows[1]["key_events"] = ["同一供词回答三条相关线索"]
    rows[1]["payoffs_due"] = ["thread-a", "thread-b", "thread-c"]

    validate_generation_plan(canon, rows)


def test_plan_rejects_null_start_for_established_chapter_three_fields():
    canon_raw = _canon()
    canon_raw["initial_state"]["char-a"].update(
        permissions=[],
        injuries=[],
        identity="守门人",
    )
    canon = normalize_canon(canon_raw)
    rows = [_plan_row(position) for position in range(1, 4)]
    rows[2]["state_transitions"] = [
        {
            "subject_id": "char-a",
            "field": field,
            "from_value": None,
            "to_value": value,
            "reason": "第三章状态变化",
        }
        for field, value in (
            ("permissions", ["archive"]),
            ("injuries", ["右臂受伤"]),
            ("identity", "档案员"),
        )
    ]

    with pytest.raises(ValueError) as exc_info:
        validate_generation_plan(canon, rows)

    message = str(exc_info.value)
    assert message.count("第 3 章状态起点不连续") == 3
    for field in ("permissions", "injuries", "identity"):
        assert f"'field': '{field}'" in message


def test_plan_allows_null_start_for_unestablished_field():
    canon = normalize_canon(_canon())
    row = _plan_row(1)
    row["state_transitions"] = [
        {
            "subject_id": "char-a",
            "field": "clearance",
            "from_value": None,
            "to_value": "archive",
            "reason": "首次建立字段",
        }
    ]

    validate_generation_plan(canon, [row])


def test_plan_diagnostic_reports_unknown_and_future_canon_refs_together():
    raw = _canon()
    raw["milestones"] = [
        {
            "id": "mile-future",
            "label": "未来节点",
            "planned_position": 2,
            "repeatable": True,
        }
    ]
    canon = normalize_canon(raw)
    rows = [_plan_row(1), _plan_row(2)]
    rows[0]["canon_refs"].extend(["canon-1", "mile-future"])

    with pytest.raises(ValueError) as exc_info:
        validate_generation_plan(canon, rows)

    message = str(exc_info.value)
    assert "第 1 章引用未知 Canon: ['canon-1']" in message
    assert "第 1 章提前引用里程碑: ['mile-future']" in message
