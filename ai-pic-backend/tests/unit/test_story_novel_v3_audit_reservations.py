import app.services.story.story_novel_v3_audit_checkpoint as audit_checkpoint
from app.models.llm_invocation import LLMInvocation
from app.models.task import TaskStatus
from app.services.story.story_novel_v3_audit_budget import (
    audit_contract_hash,
    lock_checkpoint_entry,
    prune_abandoned_reservations,
    reserve_audit_attempt,
)
from app.services.story.story_novel_v3_audit_checkpoint import (
    prepare_checkpoint_audit,
    reservation_metrics,
)
from tests.unit.story_novel_v3_test_support import persisted_stage_text
from tests.unit.test_story_novel_longform import _setup


def _reservation(stage, task_id=None):
    return {
        "reservation_id": stage.rsplit(".", 1)[-1],
        "budget_hash": "budget",
        "stage": stage,
        "task_id": task_id,
        "status": "reserved",
    }


def test_checkpoint_lock_merges_live_reservations(db_session):
    _user, _story, service, revision, task, *_ = _setup(db_session, with_character=True)
    first = _reservation("audit.1.budget.body.body.r01", task.id)
    second = _reservation("audit.1.budget.body.body.r02", task.id)
    revision.continuity_ledger = {
        "chapters": {
            "1": {
                "audit_budget_hash": "budget",
                "audit_reservations": [first, second],
            }
        }
    }
    db_session.commit()
    stale = {"audit_budget_hash": "budget", "audit_reservations": [first]}

    locked = lock_checkpoint_entry(service, revision, 1, stale)

    assert locked.id == revision.id
    assert stale["audit_reservations"] == [first, second]
    db_session.rollback()


def test_checkpoint_lock_rejects_live_body_chain_drift(db_session):
    _user, _story, service, revision, _task, *_ = _setup(
        db_session, with_character=True
    )
    live = {
        "body_hash": "body-b",
        "audit_budget_hash": "budget-b",
        "audit_contract_hash": "contract-b",
        "chapter_contract_hash": "chapter",
        "context_hash": "context",
        "canon_hash": "canon",
        "state_before_hash": "state",
        "audit_reservations": [],
    }
    revision.continuity_ledger = {"chapters": {"1": live}}
    db_session.commit()
    stale = {**live, "body_hash": "body-a", "audit_budget_hash": "budget-a"}

    try:
        lock_checkpoint_entry(service, revision, 1, stale)
    except ValueError as exc:
        assert "旧 worker" in str(exc)
    else:
        raise AssertionError("stale body chain must fail closed")
    db_session.rollback()


def test_checkpoint_rejects_unfinished_reservation(db_session):
    _user, _story, _service, revision, task, *_ = _setup(
        db_session, with_character=True
    )
    entry = {
        "audit_budget_hash": "budget",
        "audit_reservations": [_reservation("audit.1.budget.body.body.r01", task.id)],
    }

    try:
        prepare_checkpoint_audit(
            db_session,
            revision.business_id,
            1,
            entry,
            "body",
            {"delta_hash": "delta"},
            {},
        )
    except ValueError as exc:
        assert "明确终态" in str(exc)
    else:
        raise AssertionError("unfinished reservation must fail closed")


def test_failed_and_successful_reservations_are_reconciled(db_session):
    _user, _story, _service, revision, task, *_ = _setup(
        db_session, with_character=True
    )
    failed_stage = "audit.1.budget.body.body.r01"
    passed_stage = "audit.1.budget.body.body.r02"
    persisted_stage_text(db_session, revision, failed_stage, "bad", 501)
    failed_row = db_session.get(LLMInvocation, 501)
    failed_row.status = "failed"
    failed_row.response_metadata = {"finish_reason": "error"}
    db_session.commit()
    persisted_stage_text(db_session, revision, passed_stage, "good", 502)
    entry = {
        "audit_budget_hash": "budget",
        "audit_reservations": [
            _reservation(failed_stage, task.id),
            _reservation(passed_stage, task.id),
        ],
    }

    recovered = reservation_metrics(db_session, revision.business_id, entry)

    assert recovered["complete"] is True
    assert [item["status"] for item in recovered["reservations"]] == [
        "failed",
        "succeeded",
    ]
    assert recovered["reservations"][0]["invocation_ids"] == [501]
    assert [item["invocation_id"] for item in recovered["attempts"]] == [502]


def test_reservation_reconciliation_uses_fresh_invocation_session(
    db_session, monkeypatch
):
    _user, _story, _service, revision, task, *_ = _setup(
        db_session, with_character=True
    )
    stage = "audit.1.budget.body.body.r01"
    persisted_stage_text(db_session, revision, stage, "good", 504)
    observed_sessions = []
    repository_type = audit_checkpoint.LLMInvocationRepository

    class RecordingRepository(repository_type):
        def __init__(self, session):
            observed_sessions.append(session)
            super().__init__(session)

    monkeypatch.setattr(
        audit_checkpoint, "LLMInvocationRepository", RecordingRepository
    )
    recovered = reservation_metrics(
        db_session,
        revision.business_id,
        {"audit_reservations": [_reservation(stage, task.id)]},
    )

    assert recovered["complete"] is True
    assert observed_sessions and observed_sessions[0] is not db_session


def test_checkpoint_requires_successful_audit_of_final_body(db_session):
    _user, _story, _service, revision, task, *_ = _setup(
        db_session, with_character=True
    )
    entry = {
        "audit_budget_hash": "budget",
        "chapter_contract_hash": "chapter",
        "context_hash": "context",
        "canon_hash": "canon",
    }
    expected = {"delta_hash": "delta"}
    final_hash = audit_contract_hash("body", expected, entry)
    stage = f"audit.1.budget.body.{final_hash}.r01"
    persisted_stage_text(db_session, revision, stage, "bad", 503)
    row = db_session.get(LLMInvocation, 503)
    row.status = "failed"
    row.response_metadata = {"finish_reason": "error"}
    db_session.commit()
    entry["audit_reservations"] = [_reservation(stage, task.id)]

    try:
        prepare_checkpoint_audit(
            db_session,
            revision.business_id,
            1,
            entry,
            "body",
            expected,
            {"audit": {"attempts": [{"invocation_id": 503}]}},
        )
    except ValueError as exc:
        assert "最终正文" in str(exc)
    else:
        raise AssertionError("failed audit cannot validate a final body")


def test_terminal_task_reservation_without_invocation_is_pruned(db_session):
    _user, _story, service, revision, task, *_ = _setup(db_session, with_character=True)
    entry = {"audit_budget_hash": "budget", "audit_contract_hash": "budget"}
    revision.continuity_ledger = {"chapters": {"1": entry}}
    db_session.commit()
    reserve_audit_attempt(
        service,
        revision,
        entry,
        1,
        "budget",
        "audit.1.budget.body.body",
        task_id=task.id,
    )
    task.status = TaskStatus.CANCELLED
    db_session.commit()

    prune_abandoned_reservations(service, revision, entry, 1, "budget", task_id=None)

    assert entry["audit_reservations"] == []
