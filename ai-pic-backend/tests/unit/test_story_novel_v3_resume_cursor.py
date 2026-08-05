from types import SimpleNamespace

import pytest
from app.services.narrative_memory.source_hash import novel_chapter_source_hash
from app.services.story.story_novel_context_utils import (
    prompt_chapter_contract,
    value_hash,
)
from app.services.story.story_novel_domain import sha256_text
from app.services.story.story_novel_resume_cursor import (
    advance_resume_cursor,
    resume_suffix_plan_rows,
)
from app.services.story.story_novel_state_service import state_hash
from fastapi import HTTPException


def test_ready_chapter_advances_resume_cursor_to_first_non_ready_position():
    revision = SimpleNamespace(
        continuity_ledger={
            "state_status": "failed",
            "stale_from_position": 1,
            "chapters": {
                "1": {"status": "ready"},
                "2": {"status": "audit"},
            },
        }
    )

    advance_resume_cursor(revision, [{"position": 1}, {"position": 2}])

    assert revision.continuity_ledger["stale_from_position"] == 2
    assert revision.continuity_ledger["state_status"] == "stale"


def test_all_ready_chapters_clear_resume_cursor():
    revision = SimpleNamespace(
        continuity_ledger={
            "state_status": "stale",
            "stale_from_position": 2,
            "chapters": {
                "1": {"status": "ready"},
                "2": {"status": "ready"},
            },
        }
    )

    advance_resume_cursor(revision, [{"position": 1}, {"position": 2}])

    assert "stale_from_position" not in revision.continuity_ledger
    assert revision.continuity_ledger["state_status"] == "ready"


def test_resume_cursor_infers_missing_cursor_and_skips_hash_valid_prefix(
    monkeypatch,
):
    row_1 = {"position": 1, "title": "第一章", "key_events": []}
    row_2 = {"position": 2, "title": "第二章", "key_events": []}
    chapter = SimpleNamespace(
        position=1,
        business_id="chapter-1",
        title="第一章",
        content_text="已经通过门禁的正文。",
        summary="摘要",
        cliffhanger="钩子",
        review_status="ready",
        is_deleted=False,
    )
    chapter.content_hash = sha256_text(chapter.content_text)
    after = {"subjects": {}}
    entry = {
        "status": "ready",
        "stage": "ready",
        "extraction_status": "ready",
        "chapter_business_id": chapter.business_id,
        "body_hash": chapter.content_hash,
        "source_hash": novel_chapter_source_hash(chapter),
        "canon_hash": "canon-hash",
        "chapter_contract_hash": value_hash(prompt_chapter_contract(row_1)),
        "state_validation": {"status": "passed"},
        "state_before_hash": "state-before",
        "state_after": after,
        "state_after_hash": state_hash(after),
        "context_hash": "old-compiler-context-hash",
        "brief_hash": "brief-hash",
        "audit_contract_hash": "audit-hash",
        "proof_spans": [],
    }
    revision = SimpleNamespace(
        generation_plan={"canon_hash": "canon-hash"},
        continuity_ledger={
            "chapters": {"1": entry},
        },
        chapters=[chapter],
    )
    monkeypatch.setattr(
        "app.services.story.story_novel_resume_cursor.candidate_checkpoint_ready",
        lambda *_args: True,
    )

    assert resume_suffix_plan_rows(SimpleNamespace(), revision, [row_1, row_2]) == [
        row_2
    ]
    assert revision.continuity_ledger["stale_from_position"] == 2
    assert revision.continuity_ledger["state_status"] == "stale"


def test_resume_cursor_rejects_invalid_prefix_instead_of_rewriting_it(monkeypatch):
    row_1 = {"position": 1, "title": "第一章", "key_events": []}
    chapter = SimpleNamespace(
        position=1,
        business_id="chapter-1",
        title="第一章",
        content_text="正文已被改变。",
        summary=None,
        cliffhanger=None,
        review_status="ready",
        content_hash="stale-body-hash",
        is_deleted=False,
    )
    revision = SimpleNamespace(
        generation_plan={"canon_hash": "canon-hash"},
        continuity_ledger={
            "stale_from_position": 2,
            "chapters": {"1": {"status": "ready"}},
        },
        chapters=[chapter],
    )
    monkeypatch.setattr(
        "app.services.story.story_novel_resume_cursor.candidate_checkpoint_ready",
        lambda *_args: True,
    )

    with pytest.raises(HTTPException) as exc_info:
        resume_suffix_plan_rows(SimpleNamespace(), revision, [row_1])
    assert "拒绝静默重写" in exc_info.value.detail
