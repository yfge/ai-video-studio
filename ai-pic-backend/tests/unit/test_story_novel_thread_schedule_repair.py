import json

from app.services.story.story_novel_thread_schedule import parse_thread_payoffs
from app.services.story.story_novel_thread_schedule_repair import (
    merge_schedule_repairs,
    repair_conflict_ids,
)


def _contract():
    return [
        {
            "position": 1,
            "open_threads": ["thread-a", "观测员下落；云井审计编号"],
            "key_events": ["打开线索"],
        },
        {
            "position": 2,
            "open_threads": [],
            "key_events": ["解决甲", "核验审计编号"],
        },
    ]


def test_patch_repair_preserves_valid_rows_and_replaces_split_id():
    original = [
        {
            "thread_id": "thread-a",
            "payoff_position": 2,
            "evidence_key_event": "解决甲",
        },
        {
            "thread_id": "观测员下落",
            "payoff_position": 2,
            "evidence_key_event": "核验审计编号",
        },
        {
            "thread_id": "云井审计编号",
            "payoff_position": 2,
            "evidence_key_event": "核验审计编号",
        },
    ]
    conflicts = repair_conflict_ids(original, _contract())
    repair = json.dumps(
        {
            "thread_payoff_repairs": [
                {
                    "thread_id": "观测员下落；云井审计编号",
                    "payoff_position": 2,
                    "evidence_key_event": "核验审计编号",
                }
            ]
        },
        ensure_ascii=False,
    )

    merged = merge_schedule_repairs(original, repair, _contract(), conflicts)
    parsed, error = parse_thread_payoffs(
        json.dumps({"thread_payoffs": merged}, ensure_ascii=False),
        _contract(),
    )

    assert conflicts == ["观测员下落；云井审计编号"]
    assert error is None
    assert parsed[0] == original[0]
    assert parsed[1]["thread_id"] == "观测员下落；云井审计编号"


def test_patch_repair_must_cover_every_conflict_once():
    original = []
    conflicts = repair_conflict_ids(original, _contract())
    incomplete = json.dumps(
        {
            "thread_payoff_repairs": [
                {
                    "thread_id": "thread-a",
                    "payoff_position": 2,
                    "evidence_key_event": "解决甲",
                }
            ]
        }
    )

    try:
        merge_schedule_repairs(original, incomplete, _contract(), conflicts)
    except ValueError as exc:
        assert "逐项且仅覆盖全部冲突" in str(exc)
    else:
        raise AssertionError("incomplete patch must fail")


def test_capacity_repair_only_moves_minimal_overflow_rows():
    contract = [
        {
            "position": 1,
            "open_threads": [f"thread-{index}" for index in range(5)],
            "key_events": ["打开线索"],
        },
        {
            "position": 2,
            "open_threads": [],
            "key_events": ["共享回答", "回答二", "回答三", "回答四"],
        },
        {"position": 3, "open_threads": [], "key_events": ["后续回答"]},
    ]
    original = [
        {
            "thread_id": f"thread-{index}",
            "payoff_position": 2,
            "evidence_key_event": (
                "共享回答" if index < 2 else f"回答{'二三四'[index - 2]}"
            ),
        }
        for index in range(5)
    ]

    assert repair_conflict_ids(original, contract) == ["thread-3", "thread-4"]
