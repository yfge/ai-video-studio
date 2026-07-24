import pytest
from app.services.story.story_novel_canon_service import normalize_canon
from app.services.story.story_novel_continuity_service import require_valid_state_chain
from app.services.story.story_novel_state_service import (
    apply_state_delta,
    initial_story_state,
    quality_metrics,
    state_hash,
)
from fastapi import HTTPException
from tests.unit.test_story_novel_continuity_v3 import (
    HARD_METRICS,
    _delta,
    _ready_v2_revision,
)
from tests.unit.test_story_novel_longform import _canon


def test_state_hash_chain_replays_each_chapter():
    canon = normalize_canon(_canon())
    first_delta = _delta("event-1")
    second_delta = _delta("event-2")
    first_state = apply_state_delta(initial_story_state(canon), first_delta)
    second_state = apply_state_delta(first_state, second_delta)
    revision = type(
        "Revision",
        (),
        {
            "generation_plan": {"canon": canon},
            "continuity_ledger": {"current_state": second_state},
        },
    )()
    chapters = [
        type("Chapter", (), {"position": 1})(),
        type("Chapter", (), {"position": 2})(),
    ]
    rows = {
        "1": {
            "status": "ready",
            "canon_hash": canon["canon_hash"],
            "state_validation": {"status": "passed"},
            "state_before_hash": state_hash(initial_story_state(canon)),
            "state_after_hash": state_hash(first_state),
            "state_delta": first_delta,
        },
        "2": {
            "status": "ready",
            "canon_hash": canon["canon_hash"],
            "state_validation": {"status": "passed"},
            "state_before_hash": state_hash(first_state),
            "state_after_hash": state_hash(second_state),
            "state_delta": second_delta,
        },
    }
    require_valid_state_chain(revision, chapters, rows)
    rows["2"]["state_before_hash"] = "stale"
    with pytest.raises(HTTPException) as exc:
        require_valid_state_chain(revision, chapters, rows)
    assert "第 2 章状态校验不完整" in str(exc.value.detail)


def test_state_hash_chain_rejects_stale_ledger_current_state(db_session):
    _user, _service, revision, chapter, canon = _ready_v2_revision(db_session)
    revision.continuity_ledger = {
        **revision.continuity_ledger,
        "current_state": initial_story_state(canon),
    }
    db_session.commit()
    with pytest.raises(HTTPException) as exc:
        require_valid_state_chain(
            revision,
            [chapter],
            revision.continuity_ledger["chapters"],
        )
    assert "current_state" in str(exc.value.detail)


def test_v3_metrics_expose_all_hard_gates(db_session):
    _user, _service, revision, _chapter, _canon_value = _ready_v2_revision(db_session)
    metrics = quality_metrics(revision)
    assert HARD_METRICS == set(metrics) - {"chapter_repair_rate"}
    assert all(metrics[key] == 0 for key in HARD_METRICS)


def test_owned_object_follows_holder_and_possessions():
    state = {
        "subjects": {
            "char-source": {"location": "loc-a", "possessions": ["obj-key"]},
            "char-target": {"location": "loc-b", "possessions": []},
            "obj-key": {"owner_id": "char-source", "location": "loc-a"},
        }
    }
    transferred = apply_state_delta(
        state,
        {
            "state_transitions": [
                {
                    "subject_id": "obj-key",
                    "field": "owner_id",
                    "to_value": "char-target",
                }
            ]
        },
    )
    moved = apply_state_delta(
        transferred,
        {
            "location_transitions": [
                {
                    "subject_id": "char-target",
                    "from_location_id": "loc-b",
                    "to_location_id": "loc-c",
                }
            ]
        },
    )

    assert "obj-key" not in moved["subjects"]["char-source"]["possessions"]
    assert moved["subjects"]["char-target"]["possessions"] == ["obj-key"]
    assert moved["subjects"]["obj-key"] == {
        "owner_id": "char-target",
        "location": "loc-c",
    }
