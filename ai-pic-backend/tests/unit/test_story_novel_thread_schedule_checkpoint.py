from app.services.story.story_novel_canon_service import content_hash
from app.services.story.story_novel_thread_schedule_checkpoint import (
    reusable_thread_payoffs,
)


def _plan(rows):
    return {
        "version": 4,
        "outline_hash": "outline-hash",
        "chapters": [
            {
                "position": 1,
                "open_threads": ["thread-a"],
                "key_events": ["打开线索"],
            },
            {
                "position": 2,
                "open_threads": [],
                "key_events": ["解决线索"],
            },
        ],
        "thread_payoffs": rows,
        "thread_payoffs_hash": content_hash(rows),
        "thread_payoffs_outline_hash": "outline-hash",
    }


def test_reuses_hash_and_outline_bound_schedule():
    rows = [
        {
            "thread_id": "thread-a",
            "payoff_position": 2,
            "evidence_key_event": "解决线索",
        }
    ]

    assert reusable_thread_payoffs(_plan(rows)) == rows


def test_rejects_stale_or_tampered_schedule_checkpoint():
    rows = [
        {
            "thread_id": "thread-a",
            "payoff_position": 2,
            "evidence_key_event": "解决线索",
        }
    ]
    stale = _plan(rows)
    stale["thread_payoffs_outline_hash"] = "old-outline"
    tampered = _plan(rows)
    tampered["thread_payoffs"][0]["payoff_position"] = 1

    assert reusable_thread_payoffs(stale) is None
    assert reusable_thread_payoffs(tampered) is None
