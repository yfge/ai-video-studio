import pytest
from app.services.story.story_novel_block_contract import assemble_prose_blocks
from app.services.story.story_novel_domain import sha256_text
from app.services.story.story_novel_expected_delta import compile_expected_delta
from app.services.story.story_novel_state_service import initial_story_state
from app.services.story.story_novel_v3_audit_budget import audit_contract_hash
from app.services.story.story_novel_v3_checkpoint import checkpoint_body
from tests.unit.story_novel_v3_test_support import persisted_stage_text
from tests.unit.test_story_novel_longform import _setup
from tests.unit.test_story_novel_v3_pipeline import _blocks, _brief, _canon, _row


def test_checkpoint_rejects_over_budget_audit_result(db_session):
    _user, _story, service, revision, _task, *_ = _setup(
        db_session, with_character=True
    )
    row = _row()
    state = initial_story_state(_canon())
    expected = compile_expected_delta(row, state)
    brief_input = {
        "expected_beat_count": 8,
        "chapter_contract": row,
        "chapter_contract_hash": "contract",
        "state_before_hash": expected["state_before_hash"],
        "input_evidence_hash": "evidence",
    }
    brief = _brief(brief_input)
    prose = {"block_contents": _blocks(8), **assemble_prose_blocks(_blocks(8))}
    audit = {
        "passed": True,
        "state_delta": expected,
        "state_after": state,
        "state_validation": {"status": "passed", "violations": []},
        "proof_spans": [],
        "sentence_index_hash": "sentences",
        "future_audit": {},
        "failed_block_ids": [],
    }
    entry = {"audit_budget_hash": "budget", "audit_reservations": []}
    final_hash = audit_contract_hash(
        sha256_text(prose["content_text"].strip()), expected, entry
    )
    attempts = []
    for index in range(1, 5):
        stage = f"audit.1.budget.body.{final_hash}.r{index:02d}"
        text = persisted_stage_text(db_session, revision, stage, "audit", 400 + index)
        attempts.append(text.invocation_evidence)
        entry["audit_reservations"].append(
            {
                "reservation_id": f"r{index:02d}",
                "budget_hash": "budget",
                "stage": stage,
                "task_id": None,
                "status": "reserved",
            }
        )
    revision.continuity_ledger = {"chapters": {"1": entry}}
    db_session.commit()

    with pytest.raises(ValueError, match="审计调用次数超过硬上限"):
        checkpoint_body(
            service,
            revision,
            1,
            row,
            entry,
            brief,
            {"chapter_brief": brief},
            expected,
            prose,
            audit,
            {"audit": {"attempts": attempts}},
            repair_count=0,
        )
    db_session.rollback()
    assert service.repo.chapters_from_position(revision.id, 1) == []
