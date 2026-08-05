import pytest
from app.models.llm_invocation import LLMInvocation
from app.services.story.story_novel_v3_audit_budget import reserve_audit_attempt
from tests.unit.story_novel_v3_test_support import persisted_stage_text
from tests.unit.test_story_novel_longform import _setup


def test_transport_failures_have_separate_bounded_audit_budget(db_session):
    _user, _story, service, revision, task, *_ = _setup(db_session, with_character=True)
    entry = {"audit_budget_hash": "budget", "audit_contract_hash": "budget"}
    revision.continuity_ledger = {"chapters": {"1": entry}}
    db_session.commit()

    for index in range(3):
        stage = reserve_audit_attempt(
            service,
            revision,
            entry,
            1,
            "budget",
            f"audit.1.budget.body.body.fail-{index}",
            task_id=task.id,
        )
        persisted_stage_text(db_session, revision, stage, "failed", 700 + index)
        row = db_session.get(LLMInvocation, 700 + index)
        row.status = "failed"
        row.response_metadata = {"finish_reason": "error"}
        db_session.commit()

    with pytest.raises(ValueError, match="传输失败次数已耗尽"):
        reserve_audit_attempt(
            service,
            revision,
            entry,
            1,
            "budget",
            "audit.1.budget.body.body.fourth",
            task_id=task.id,
        )


def test_failed_transport_does_not_consume_substantive_audit_slot(db_session):
    _user, _story, service, revision, task, *_ = _setup(db_session, with_character=True)
    entry = {"audit_budget_hash": "budget", "audit_contract_hash": "budget"}
    revision.continuity_ledger = {"chapters": {"1": entry}}
    db_session.commit()
    failed_stage = reserve_audit_attempt(
        service,
        revision,
        entry,
        1,
        "budget",
        "audit.1.budget.body.body.failed",
        task_id=task.id,
    )
    persisted_stage_text(db_session, revision, failed_stage, "failed", 710)
    row = db_session.get(LLMInvocation, 710)
    row.status = "failed"
    row.response_metadata = {"finish_reason": "error"}
    db_session.commit()

    next_stage = reserve_audit_attempt(
        service,
        revision,
        entry,
        1,
        "budget",
        "audit.1.budget.body.body.retry",
        task_id=task.id,
    )

    assert next_stage.endswith(entry["audit_reservations"][-1]["reservation_id"])
    assert len(entry["audit_reservations"]) == 2
