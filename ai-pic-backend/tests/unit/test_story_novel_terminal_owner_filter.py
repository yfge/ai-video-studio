import json

import pytest
from app.services.story.story_novel_canon_service import (
    CANON_GATE_VERSION,
    normalize_canon,
    parse_model_canon,
)
from tests.unit.test_story_novel_milestone_outcomes import _canon, _outcome


def _contract(chapter_count: int = 48) -> dict:
    return {
        "story_seed": {
            "structured_outline": {
                "chapters": [
                    {
                        "position": position,
                        "title": f"第{position}章",
                        "goal": "推进",
                        "key_events": [
                            (
                                "2174-08-03 08:00 故事开始"
                                if position == 1
                                else f"第{position}章事件"
                            )
                        ],
                        "end_state": "继续",
                    }
                    for position in range(1, chapter_count + 1)
                ]
            },
            "world_constraints": [],
        }
    }


def _terminal_canon(*outcomes: dict, subject_id: str = "obj-zero-wind-key"):
    canon = _canon()
    canon["milestones"].append(
        {
            "id": "mile-key-destroyed",
            "label": "唯一风钥熔毁",
            "planned_position": 45,
            "repeatable": False,
            "outcomes": list(outcomes) or [_outcome(subject_id, "status", "destroyed")],
        }
    )
    return canon


def _parse(canon: dict):
    return parse_model_canon(
        json.dumps(canon, ensure_ascii=False),
        _contract(),
    )


def test_model_parser_completes_terminal_owner_clear_with_diagnostic():
    canon, error, diagnostics = _parse(_terminal_canon())

    assert error is None
    assert canon["milestones"][-1]["outcomes"] == [
        _outcome("obj-zero-wind-key", "status", "destroyed"),
        _outcome("obj-zero-wind-key", "owner_id", None),
    ]
    assert diagnostics == [
        {
            "id": "mile-key-destroyed",
            "section": "milestone",
            "reason": "terminal_owner_clear_completed",
            "subject_id": "obj-zero-wind-key",
        }
    ]


def test_raw_normalizer_still_rejects_missing_terminal_owner_clear():
    with pytest.raises(ValueError, match="必须清空 owner_id"):
        normalize_canon(
            _terminal_canon(),
            required_gate_version=CANON_GATE_VERSION,
        )


def test_existing_terminal_owner_clear_is_unchanged():
    raw = _terminal_canon(
        _outcome("obj-zero-wind-key", "status", "destroyed"),
        _outcome("obj-zero-wind-key", "owner_id", None),
    )

    canon, error, diagnostics = _parse(raw)

    assert error is None
    assert canon["milestones"][-1]["outcomes"] == raw["milestones"][-1]["outcomes"]
    assert diagnostics == []


def test_non_terminal_status_does_not_complete_owner():
    canon, error, diagnostics = _parse(
        _terminal_canon(_outcome("obj-zero-wind-key", "status", "archived"))
    )

    assert error is None
    assert len(canon["milestones"][-1]["outcomes"]) == 1
    assert diagnostics == []


def test_non_object_terminal_status_does_not_complete_owner():
    canon, error, diagnostics = _parse(_terminal_canon(subject_id="char-li-yan"))

    assert error is None
    assert len(canon["milestones"][-1]["outcomes"]) == 1
    assert diagnostics == []


def test_conflicting_terminal_owner_still_fails_closed():
    canon, error, diagnostics = _parse(
        _terminal_canon(
            _outcome("obj-zero-wind-key", "status", "destroyed"),
            _outcome("obj-zero-wind-key", "owner_id", "char-li-yan"),
        )
    )

    assert canon is None
    assert "必须清空 owner_id" in error
    assert diagnostics == []


def test_initial_null_owner_without_prior_transfer_still_fails_future_gate():
    raw = _terminal_canon()
    raw["milestones"] = [
        item for item in raw["milestones"] if item["id"] != "mile-key-transfer"
    ]

    canon, error, diagnostics = _parse(raw)

    assert canon is None
    assert "状态提前包含未来里程碑结果" in error
    assert diagnostics[0]["reason"] == "terminal_owner_clear_completed"


def test_terminal_completion_leaves_later_archive_milestone_unchanged():
    raw = _terminal_canon()
    archive = {
        "id": "mile-key-archived",
        "label": "熔毁记录归档",
        "planned_position": 48,
        "repeatable": False,
        "outcomes": [_outcome("obj-zero-wind-key", "status", "archived")],
    }
    raw["milestones"].append(archive)

    canon, error, _diagnostics = _parse(raw)

    assert error is None
    assert canon["milestones"][-1] == archive
