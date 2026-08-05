from app.services.story import story_novel_v3_audit_contract as audit_contract
from app.services.story.story_novel_v3_audit_contract import (
    AUDIT_INPUT_VERSION,
    AUDIT_VALIDATION_VERSION,
    audit_contract_hash,
    ensure_audit_contract,
)
from tests.unit.test_story_novel_longform import _setup


def test_old_audit_input_contract_is_archived_and_reset_once(db_session, monkeypatch):
    _user, _story, service, revision, *_ = _setup(db_session, with_character=True)
    expected_delta = {"delta_hash": "delta"}
    entry = {
        "body_hash": "body",
        "chapter_contract_hash": "chapter",
        "context_hash": "context",
        "canon_hash": "canon",
        "state_before_hash": "state",
        "audit_reservations": [
            {"reservation_id": f"r0{index}"} for index in range(1, 4)
        ],
        "stage_metrics": {"audit": {"calls": 3}, "prose": {"calls": 1}},
    }
    monkeypatch.setattr(
        audit_contract, "AUDIT_VALIDATION_VERSION", AUDIT_VALIDATION_VERSION - 1
    )
    old_hash = audit_contract_hash("body", expected_delta, entry)
    entry.update(audit_contract_hash=old_hash, audit_budget_hash=old_hash)
    revision.continuity_ledger = {"chapters": {"18": entry}}
    db_session.commit()
    monkeypatch.setattr(
        audit_contract, "AUDIT_VALIDATION_VERSION", AUDIT_VALIDATION_VERSION
    )
    new_hash = audit_contract_hash("body", expected_delta, entry)
    assert new_hash != old_hash

    assert ensure_audit_contract(service, revision, entry, 18, new_hash) == new_hash
    db_session.refresh(revision)
    stored = revision.continuity_ledger["chapters"]["18"]
    assert stored["body_hash"] == "body"
    assert stored["audit_input_version"] == AUDIT_INPUT_VERSION
    assert stored["audit_validation_version"] == AUDIT_VALIDATION_VERSION
    assert stored["audit_contract_hash"] == new_hash
    assert stored["audit_budget_hash"] == new_hash
    assert stored["audit_reservations"] == []
    assert stored["stage_metrics"] == {"prose": {"calls": 1}}
    assert stored["audit_contract_history"][0]["audit_budget_hash"] == old_hash

    assert ensure_audit_contract(service, revision, entry, 18, new_hash) == new_hash
    db_session.refresh(revision)
    assert (
        len(revision.continuity_ledger["chapters"]["18"]["audit_contract_history"]) == 1
    )


def test_audit_contract_upgrade_rejects_body_chain_drift(db_session):
    _user, _story, service, revision, *_ = _setup(db_session, with_character=True)
    revision.continuity_ledger = {
        "chapters": {
            "18": {
                "body_hash": "live-body",
                "chapter_contract_hash": "chapter",
                "context_hash": "context",
                "canon_hash": "canon",
                "state_before_hash": "state",
                "audit_contract_hash": "old",
            }
        }
    }
    db_session.commit()
    stale = {
        "body_hash": "stale-body",
        "chapter_contract_hash": "chapter",
        "context_hash": "context",
        "canon_hash": "canon",
        "state_before_hash": "state",
        "audit_contract_hash": "old",
    }

    try:
        ensure_audit_contract(service, revision, stale, 18, "new")
    except ValueError as exc:
        assert "正文或上下文链已变化" in str(exc)
    else:
        raise AssertionError("stale body chain must be rejected")
