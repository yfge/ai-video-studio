import pytest
from app.services.story.story_novel_block_contract import assemble_prose_blocks
from app.services.story.story_novel_expected_delta import compile_expected_delta
from app.services.story.story_novel_v3_checkpoint import checkpoint_prose
from tests.unit.test_story_novel_longform import _setup
from tests.unit.test_story_novel_v3_pipeline import _blocks, _brief, _row


def test_v3_body_and_ledger_rollback_together_on_checkpoint_failure(
    db_session, monkeypatch
):
    _user, _story, service, revision, _task, *_ = _setup(
        db_session, with_character=True
    )
    row = _row()
    state = {
        "subjects": {"char-a": {"location": "loc-gate", "knowledge": []}},
        "occurred_event_ids": [],
        "completed_milestone_ids": [],
        "threads": {},
    }
    expected = compile_expected_delta(row, state)
    brief_input = {
        "expected_beat_count": 8,
        "chapter_contract": row,
        "chapter_contract_hash": "contract",
        "state_before_hash": expected["state_before_hash"],
        "input_evidence_hash": "evidence",
    }
    brief = _brief(brief_input)
    prose = assemble_prose_blocks(_blocks(8))
    prose["block_contents"] = _blocks(8)

    def fail_ledger(*_args, **_kwargs):
        raise RuntimeError("ledger write failed")

    monkeypatch.setattr(
        "app.services.story.story_novel_chapter_service.save_ledger_entry",
        fail_ledger,
    )
    with pytest.raises(RuntimeError, match="ledger write failed"):
        checkpoint_prose(
            service,
            revision,
            1,
            row,
            {},
            brief,
            {"chapter_brief": brief},
            expected,
            prose,
            {"calls": 1},
        )
    db_session.rollback()

    assert service.repo.chapters_from_position(revision.id, 1) == []
