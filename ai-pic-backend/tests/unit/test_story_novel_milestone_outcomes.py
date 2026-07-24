import pytest
from app.services.story.story_novel_canon_service import (
    CANON_GATE_VERSION,
    normalize_canon,
)


def _outcome(subject_id: str, field: str, value, operator: str = "eq") -> dict:
    return {
        "subject_id": subject_id,
        "field": field,
        "operator": operator,
        "value": value,
    }


def _milestone(item_id: str, position: int, outcome: dict) -> dict:
    return {
        "id": item_id,
        "label": item_id,
        "planned_position": position,
        "repeatable": False,
        "outcomes": [outcome],
    }


def _canon() -> dict:
    objects = (
        "obj-zero-wind-key",
        "obj-r17-sample",
        "obj-ticket-18h",
        "obj-empty-wagon-records",
    )
    return {
        "gate_version": CANON_GATE_VERSION,
        "timeline": [
            {
                "id": "time-start",
                "label": "2174-08-03 08:00 故事开始",
                "order": 1,
                "story_time": "2174-08-03 08:00",
                "immutable": True,
                "source_chapter_position": 1,
                "source_key_event": "2174-08-03 08:00 故事开始",
            }
        ],
        "entities": [
            {
                "id": "char-li-yan",
                "kind": "character",
                "name": "黎雁",
                "aliases": [],
                "attributes": {},
            },
            {
                "id": "loc-port",
                "kind": "location",
                "name": "澄砂港",
                "aliases": [],
                "attributes": {},
            },
            *[
                {
                    "id": item_id,
                    "kind": "object",
                    "name": item_id,
                    "aliases": [],
                    "attributes": {},
                }
                for item_id in objects
            ],
        ],
        "world_rules": [],
        "milestones": [
            _milestone(
                "mile-key-transfer",
                1,
                _outcome("obj-zero-wind-key", "owner_id", "char-li-yan"),
            ),
            _milestone(
                "mile-window-announced",
                1,
                _outcome(
                    "char-li-yan",
                    "knowledge",
                    "fact-window-closes",
                    "contains",
                ),
            ),
            _milestone(
                "mile-r17-collected",
                2,
                _outcome("obj-r17-sample", "status", "sealed-r17"),
            ),
            _milestone(
                "mile-empty-wagons-found",
                5,
                _outcome("obj-empty-wagon-records", "status", "evidence-obtained"),
            ),
            _milestone(
                "mile-ticket-obtained",
                7,
                _outcome("obj-ticket-18h", "owner_id", "char-li-yan"),
            ),
        ],
        "character_arcs": [],
        "initial_state": {
            "char-li-yan": {
                "location": "loc-port",
                "knowledge": [],
                "possessions": [],
            },
            **{
                item_id: {
                    "location": "loc-port",
                    "owner_id": None,
                    "status": "not-obtained",
                }
                for item_id in objects
            },
        },
    }


def test_clean_chapter_zero_state_passes_gate_v1():
    canon = normalize_canon(_canon(), required_gate_version=CANON_GATE_VERSION)

    assert canon["gate_version"] == CANON_GATE_VERSION
    assert len(canon["canon_hash"]) == 64


@pytest.mark.parametrize(
    ("subject_id", "field", "value", "milestone_id"),
    [
        (
            "obj-zero-wind-key",
            "owner_id",
            "char-li-yan",
            "mile-key-transfer",
        ),
        (
            "char-li-yan",
            "knowledge",
            ["fact-window-closes"],
            "mile-window-announced",
        ),
        ("obj-r17-sample", "status", "sealed-r17", "mile-r17-collected"),
        (
            "obj-empty-wagon-records",
            "status",
            "evidence-obtained",
            "mile-empty-wagons-found",
        ),
        (
            "obj-ticket-18h",
            "owner_id",
            "char-li-yan",
            "mile-ticket-obtained",
        ),
    ],
)
def test_gate_v1_rejects_future_results_in_initial_state(
    subject_id: str,
    field: str,
    value,
    milestone_id: str,
):
    value_with_future = _canon()
    value_with_future["initial_state"][subject_id][field] = value

    with pytest.raises(ValueError, match=milestone_id):
        normalize_canon(
            value_with_future,
            required_gate_version=CANON_GATE_VERSION,
        )


def test_chapter_zero_reports_all_future_milestone_results_together():
    polluted = _canon()
    polluted["milestones"][0]["id"] = "mile-1"
    polluted["milestones"][2]["id"] = "mile-3"
    polluted["initial_state"]["obj-zero-wind-key"]["owner_id"] = "char-li-yan"
    polluted["initial_state"]["obj-r17-sample"]["status"] = "sealed-r17"

    with pytest.raises(ValueError) as exc_info:
        normalize_canon(polluted, required_gate_version=CANON_GATE_VERSION)

    message = str(exc_info.value)
    assert "mile-1" in message
    assert "mile-3" in message


def test_gate_v1_aggregates_duplicate_outcomes_and_chapter_zero_violations():
    duplicate = _canon()
    duplicate["milestones"][0]["id"] = "mile-1"
    duplicate["milestones"][2]["id"] = "mile-3"
    duplicate["milestones"].append(
        _milestone(
            "mile-22",
            22,
            _outcome("obj-zero-wind-key", "owner_id", "char-li-yan"),
        )
    )
    duplicate["initial_state"]["obj-r17-sample"]["status"] = "sealed-r17"

    with pytest.raises(ValueError) as exc_info:
        normalize_canon(duplicate, required_gate_version=CANON_GATE_VERSION)

    message = str(exc_info.value)
    assert "重复 milestone outcome" in message
    assert "状态提前包含未来里程碑结果" in message
    assert "mile-1" in message
    assert "mile-3" in message
    assert "mile-22" in message


def test_terminal_object_milestone_requires_owner_to_be_cleared():
    canon = _canon()
    canon["milestones"] = [
        item for item in canon["milestones"] if item["id"] != "mile-key-transfer"
    ]
    canon["initial_state"]["obj-zero-wind-key"]["owner_id"] = "char-li-yan"
    canon["milestones"].append(
        {
            "id": "mile-key-destroyed",
            "label": "唯一风钥熔毁",
            "planned_position": 45,
            "repeatable": False,
            "outcomes": [
                _outcome("obj-zero-wind-key", "status", "destroyed"),
            ],
        }
    )

    with pytest.raises(ValueError, match="必须清空 owner_id"):
        normalize_canon(canon, required_gate_version=CANON_GATE_VERSION)

    canon["milestones"][-1]["outcomes"].append(
        _outcome("obj-zero-wind-key", "owner_id", None)
    )
    normalized = normalize_canon(canon, required_gate_version=CANON_GATE_VERSION)

    assert normalized["milestones"][-1]["outcomes"][-1]["value"] is None


def test_terminal_owner_clear_allows_an_intervening_transfer():
    canon = _canon()
    canon["milestones"].append(
        {
            "id": "mile-key-destroyed",
            "label": "唯一风钥熔毁",
            "planned_position": 45,
            "repeatable": False,
            "outcomes": [
                _outcome("obj-zero-wind-key", "status", "destroyed"),
                _outcome("obj-zero-wind-key", "owner_id", None),
            ],
        }
    )

    normalized = normalize_canon(
        canon,
        required_gate_version=CANON_GATE_VERSION,
    )

    assert normalized["milestones"][-1]["id"] == "mile-key-destroyed"
