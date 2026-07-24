import json

import pytest
from app.schemas.story_seed import StorySeedStructuredOutline
from app.services.story.story_seed_thread_contract import validate_seed_thread_contract
from app.services.story.story_seed_thread_repair import (
    _assigned_positions,
    apply_seed_thread_repairs,
    repair_conflict_ids,
    seed_thread_repair_prompt,
)


def _outline(thread_count=5):
    thread_ids = [f"thread-{index}" for index in range(thread_count)]
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


def test_overflow_marks_only_minimal_surplus_rows():
    outline = _outline()

    conflicts = repair_conflict_ids(outline)

    assert conflicts == ["thread-3", "thread-4"]
    prompt = seed_thread_repair_prompt(outline, conflicts, "第 2 章超过上限")
    assert '"authoritative_conflict_thread_ids":["thread-3","thread-4"]' in prompt
    assert prompt.count('"assigned_payoff_position":3') == 2
    assert '"target_chapter"' in prompt


def test_repair_assignment_never_moves_a_payoff_before_model_position():
    data = {
        "chapters": [{"position": position} for position in range(1, 6)],
        "thread_payoffs": [
            {
                "thread_id": "thread-late",
                "payoff_position": 3,
                "evidence_key_event": "answer",
            }
        ],
    }

    assigned = _assigned_positions(
        data,
        ["thread-late"],
        {"thread-late": 1},
        {3: 3, 4: 3},
    )

    assert assigned == {"thread-late": 5}


def test_patch_rejects_previous_assignment_when_chapter_has_no_slot():
    outline = _outline()

    with pytest.raises(ValueError, match="未使用系统预留的修复章节"):
        apply_seed_thread_repairs(
            outline,
            _repair(
                [
                    {
                        "thread_id": "thread-3",
                        "payoff_position": 2,
                        "evidence_key_event": (
                            "关于“thread-3”的最终证据确认：回答 thread-3"
                        ),
                    },
                    {
                        "thread_id": "thread-4",
                        "payoff_position": 3,
                        "evidence_key_event": "回答 thread-4",
                    },
                ]
            ),
            ["thread-3", "thread-4"],
        )


def test_patch_rejects_unrelated_or_reused_target_event():
    outline = _outline()
    rows = [
        {
            "thread_id": "thread-3",
            "payoff_position": 3,
            "evidence_key_event": "既有后续事件",
        },
        {
            "thread_id": "thread-4",
            "payoff_position": 3,
            "evidence_key_event": "回答 thread-4",
        },
    ]

    with pytest.raises(ValueError, match="加入了未授权事实"):
        apply_seed_thread_repairs(
            outline,
            _repair(rows),
            ["thread-3", "thread-4"],
        )


def test_patch_adds_new_evidence_preserves_other_rows_and_validates():
    outline = _outline()
    original_rows = [row.model_dump() for row in outline.thread_payoffs]
    conflicts = repair_conflict_ids(outline)

    repaired = apply_seed_thread_repairs(
        outline,
        _repair(
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
        ),
        conflicts,
    )

    assert repaired.chapters[2].key_events == [
        "既有后续事件",
        "关于“thread-3”的最终证据确认：回答 thread-3",
        "关于“thread-4”的最终证据确认：回答 thread-4",
    ]
    assert "关于“thread-3”的最终证据确认：回答 thread-3" not in (
        repaired.chapters[1].key_events
    )
    assert "关于“thread-4”的最终证据确认：回答 thread-4" not in (
        repaired.chapters[1].key_events
    )
    assert [row.model_dump() for row in repaired.thread_payoffs[:3]] == original_rows[
        :3
    ]
    assert validate_seed_thread_contract(repaired, require_version=True)
    assert outline.chapters[2].key_events == ["既有后续事件"]


@pytest.mark.parametrize(
    "rows",
    [
        [
            {
                "thread_id": "thread-3",
                "payoff_position": 3,
                "evidence_key_event": "回答 thread-3",
            }
        ],
        [
            {
                "thread_id": "thread-3",
                "payoff_position": 3,
                "evidence_key_event": "回答 thread-3",
            },
            {
                "thread_id": "thread-4",
                "payoff_position": 3,
                "evidence_key_event": "回答 thread-4",
            },
            {
                "thread_id": "thread-extra",
                "payoff_position": 3,
                "evidence_key_event": "回答 extra",
            },
        ],
        [
            {
                "thread_id": "thread-3",
                "payoff_position": 3,
                "evidence_key_event": "回答 thread-3",
            },
            {
                "thread_id": "thread-3",
                "payoff_position": 3,
                "evidence_key_event": "重复回答 thread-3",
            },
        ],
    ],
)
def test_patch_must_cover_exact_conflict_set_once(rows):
    outline = _outline()

    with pytest.raises(ValueError, match="逐项且仅覆盖全部冲突"):
        apply_seed_thread_repairs(
            outline,
            _repair(rows),
            ["thread-3", "thread-4"],
        )
