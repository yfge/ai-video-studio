"""Validate and advance the persisted resume cursor."""

from app.services.narrative_memory.source_hash import novel_chapter_source_hash
from fastapi import HTTPException

from .story_novel_context_utils import prompt_chapter_contract, value_hash
from .story_novel_domain import active_chapters, sha256_text
from .story_novel_state_service import state_hash
from .story_novel_v3_resume import proofs_match_body
from .story_novel_v3_runtime import candidate_checkpoint_ready


def resume_suffix_plan_rows(service, revision, plan_rows: list[dict]) -> list[dict]:
    """Skip an immutable ready prefix or fail before any provider call."""
    ledger = dict(revision.continuity_ledger or {})
    entries = ledger.get("chapters") or {}
    cursor = int(
        ledger.get("stale_from_position")
        or _first_non_ready_position(entries, plan_rows)
    )
    if cursor <= 1:
        return plan_rows
    chapters = {item.position: item for item in active_chapters(revision)}
    canon_hash = (revision.generation_plan or {}).get("canon_hash")
    previous_after_hash = None
    for row in sorted(plan_rows, key=lambda item: int(item["position"])):
        position = int(row["position"])
        if position >= cursor:
            break
        entry = entries.get(str(position)) or {}
        chapter = chapters.get(position)
        valid = bool(
            chapter
            and chapter.review_status == "ready"
            and entry.get("status") == "ready"
            and entry.get("stage") == "ready"
            and entry.get("extraction_status") == "ready"
            and entry.get("chapter_business_id") == chapter.business_id
            and chapter.content_hash == sha256_text(chapter.content_text)
            and entry.get("body_hash") == chapter.content_hash
            and entry.get("source_hash") == novel_chapter_source_hash(chapter)
            and entry.get("canon_hash") == canon_hash
            and entry.get("chapter_contract_hash")
            == value_hash(prompt_chapter_contract(row))
            and (entry.get("state_validation") or {}).get("status") == "passed"
            and entry.get("state_before_hash")
            and entry.get("state_after_hash") == state_hash(entry.get("state_after"))
            and entry.get("context_hash")
            and entry.get("brief_hash")
            and entry.get("audit_contract_hash")
            and proofs_match_body(entry, chapter)
            and candidate_checkpoint_ready(service, revision, chapter, entry)
            and (
                previous_after_hash is None
                or entry.get("state_before_hash") == previous_after_hash
            )
        )
        if not valid:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"第 {position} 章位于 Resume 起点 {cursor} 之前，"
                    "但 ready checkpoint/hash/状态链不完整；拒绝静默重写"
                ),
            )
        previous_after_hash = entry["state_after_hash"]
    if ledger.get("stale_from_position") is None:
        ledger.update(state_status="stale", stale_from_position=cursor)
        revision.continuity_ledger = ledger
    return [row for row in plan_rows if int(row["position"]) >= cursor]


def _first_non_ready_position(entries: dict, plan_rows: list[dict]) -> int:
    positions = sorted(int(row["position"]) for row in plan_rows)
    return next(
        (
            position
            for position in positions
            if (entries.get(str(position)) or {}).get("status") != "ready"
        ),
        (positions[-1] + 1) if positions else 1,
    )


def advance_resume_cursor(revision, plan_rows) -> None:
    ledger = dict(revision.continuity_ledger or {})
    if ledger.get("stale_from_position") is None:
        return
    entries = ledger.get("chapters") or {}
    pending = [
        int(row["position"])
        for row in plan_rows
        if (entries.get(str(row["position"])) or {}).get("status") != "ready"
    ]
    if pending:
        ledger.update(state_status="stale", stale_from_position=min(pending))
    else:
        ledger["state_status"] = "ready"
        ledger.pop("stale_from_position", None)
    revision.continuity_ledger = ledger
