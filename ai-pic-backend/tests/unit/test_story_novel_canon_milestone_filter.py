import json

from app.services.story.story_novel_canon_service import (
    normalize_canon,
    parse_model_canon,
)
from app.services.story.story_novel_plan_checkpoint import (
    begin_planning,
    reusable_generation_plan,
)
from tests.unit.test_story_novel_longform import _canon, _plan_row, _setup


def _raw_canon_with_archive_milestone():
    raw = _canon()
    raw["timeline"] = []
    raw["entities"].extend(
        [
            {
                "id": "obj-probe",
                "kind": "object",
                "name": "潮汐测针",
                "aliases": [],
                "attributes": {},
            },
            {
                "id": "loc-archive",
                "kind": "location",
                "name": "归航档案馆",
                "aliases": [],
                "attributes": {},
            },
        ]
    )
    raw["initial_state"]["obj-probe"] = {
        "location": "loc-gate",
        "owner_id": "char-a",
        "status": "intact",
    }
    raw["initial_state"]["char-a"]["possessions"] = ["obj-probe"]
    raw["milestones"] = [
        {
            "id": "mile-archive",
            "label": "正式归档",
            "planned_position": 2,
            "repeatable": False,
            "outcomes": [
                {
                    "subject_id": "obj-probe",
                    "field": "location",
                    "operator": "eq",
                    "value": "loc-archive",
                },
                {
                    "subject_id": "obj-probe",
                    "field": "status",
                    "operator": "eq",
                    "value": "archived",
                },
            ],
        }
    ]
    return raw


def _contract(first_key_event: str, milestone_key_event: str):
    return {
        "story_seed": {
            "structured_outline": {
                "chapters": [
                    {
                        "position": 1,
                        "title": "抵达",
                        "goal": "进入档案馆",
                        "key_events": [first_key_event],
                        "end_state": "等待正式归档",
                    },
                    {
                        "position": 2,
                        "title": "归档",
                        "key_events": [milestone_key_event],
                    },
                ]
            },
            "world_constraints": [],
        }
    }


def test_model_parser_drops_object_location_already_sourced_earlier():
    raw = _raw_canon_with_archive_milestone()

    canon, error, diagnostics = parse_model_canon(
        json.dumps(raw, ensure_ascii=False),
        _contract(
            "携带潮汐测针进入归航档案馆",
            "潮汐测针在归航档案馆正式归档",
        ),
    )

    assert error is None
    assert canon["milestones"][0]["outcomes"] == [
        {
            "subject_id": "obj-probe",
            "field": "status",
            "operator": "eq",
            "value": "archived",
        }
    ]
    assert diagnostics == [
        {
            "id": "mile-archive",
            "section": "milestone",
            "reason": "location_already_sourced_earlier",
            "source_chapter_position": 1,
            "subject_id": "obj-probe",
            "location_id": "loc-archive",
        }
    ]
    assert len(normalize_canon(raw)["milestones"][0]["outcomes"]) == 2


def test_model_parser_drops_location_without_milestone_chapter_source():
    raw = _raw_canon_with_archive_milestone()

    canon, error, diagnostics = parse_model_canon(
        json.dumps(raw, ensure_ascii=False),
        _contract("王明进入归航档案馆", "潮汐测针正式归档"),
    )

    assert error is None
    assert len(canon["milestones"][0]["outcomes"]) == 1
    assert diagnostics == [
        {
            "id": "mile-archive",
            "section": "milestone",
            "reason": "location_not_sourced_at_milestone",
            "planned_chapter_position": 2,
            "subject_id": "obj-probe",
            "location_id": "loc-archive",
        }
    ]


def test_model_parser_keeps_location_sourced_only_at_milestone_chapter():
    raw = _raw_canon_with_archive_milestone()

    canon, error, diagnostics = parse_model_canon(
        json.dumps(raw, ensure_ascii=False),
        _contract(
            "王明检查出发清单",
            "潮汐测针在归航档案馆正式归档",
        ),
    )

    assert error is None
    assert len(canon["milestones"][0]["outcomes"]) == 2
    assert diagnostics == []


def test_old_filter_checkpoint_recompiles_canon(db_session):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    canon = normalize_canon(_canon())
    current = {
        "schema": "story_novel_generation_plan.v2",
        "version": 4,
        "status": "planning",
        "phase": "chapters",
        "outline_hash": "outline-hash",
        "canon": canon,
        "canon_hash": canon["canon_hash"],
        "canon_gate_version": canon["gate_version"],
        "chapters": [_plan_row(1)],
    }
    revision.generation_plan = current

    assert reusable_generation_plan(current, current) is False
    resumed = begin_planning(service, revision, task, current, current)

    assert resumed is False
    assert revision.generation_plan["phase"] == "canon"
    assert "canon" not in revision.generation_plan
