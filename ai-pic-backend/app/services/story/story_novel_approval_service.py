"""Approval boundary for a complete long-form novel revision."""

from datetime import datetime

from app.models.story_novel_export import StoryNovelExport
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.services.narrative_memory.candidate_service import CandidateService
from app.services.narrative_memory.source_hash import novel_chapter_source_hash
from fastapi import HTTPException

from .story_novel_candidate_refresh import retire_revision_candidates
from .story_novel_chapter_gate import chapter_length_range
from .story_novel_chapter_service import non_whitespace_chars, source_candidates
from .story_novel_domain import active_chapters
from .story_novel_frozen_plan_gate import require_current_frozen_plan
from .story_novel_plan_versions import (
    is_state_gated_plan,
    is_v3_plan,
    is_v4_plan,
    is_v5_plan,
)
from .story_novel_v2_approval import require_v2_quality
from .story_novel_v3_approval import require_v3_quality
from .story_novel_v4_approval import require_v4_quality
from .story_novel_v5_projection import project_v5_revision
from .story_novel_v5_quality import require_v5_quality


def approve_revision(service, revision):
    chapters = _require_complete_chapters(revision)
    plan = dict(revision.generation_plan or {})
    ledger_rows = (revision.continuity_ledger or {}).get("chapters") or {}
    _require_lengths(chapters, plan)
    eligible_candidate_ids = _require_extraction(
        service, revision, chapters, ledger_rows
    )
    if is_v5_plan(plan):
        require_current_frozen_plan(revision, plan)
        require_v5_quality(service.db, revision, chapters, ledger_rows)
    elif is_state_gated_plan(plan):
        require_current_frozen_plan(revision, plan)
        require_v2_quality(revision, chapters, ledger_rows)
    if is_v4_plan(plan):
        require_v4_quality(service.db, revision, chapters, ledger_rows)
    elif is_v3_plan(plan):
        require_v3_quality(service.db, revision, chapters, ledger_rows)
    _require_current_report(revision, chapters)
    if is_v5_plan(plan):
        eligible_candidate_ids = project_v5_revision(
            service, revision, chapters, ledger_rows
        )
    _promote_revision(service, revision, chapters, eligible_candidate_ids)
    return revision


def _require_complete_chapters(revision):
    chapters = active_chapters(revision)
    if len(chapters) != int(revision.chapter_count or 0) or any(
        row.review_status not in {"ready", "target_changed"} for row in chapters
    ):
        raise HTTPException(status_code=409, detail="仍有待复核章节")
    if [row.position for row in chapters] != list(range(1, len(chapters) + 1)):
        raise HTTPException(status_code=409, detail="章节顺序不是从1开始的连续编号")
    return chapters


def _require_lengths(chapters, plan: dict) -> None:
    plan_rows = {int(item["position"]): item for item in plan.get("chapters") or []}
    invalid_lengths = [
        row.position
        for row in chapters
        if row.position not in plan_rows
        or not chapter_length_range(plan_rows[row.position])[0]
        <= non_whitespace_chars(row.content_text)
        <= chapter_length_range(plan_rows[row.position])[2]
    ]
    if invalid_lengths:
        raise HTTPException(
            status_code=409, detail=f"章节长度不合格: {invalid_lengths}"
        )


def _require_extraction(service, revision, chapters, ledger_rows) -> set[str] | None:
    invalid_extraction = [
        row.position
        for row in chapters
        if (
            (ledger_rows.get(str(row.position)) or {}).get("extraction_status")
            != "ready"
            or (ledger_rows.get(str(row.position)) or {}).get("body_hash")
            != row.content_hash
            or (ledger_rows.get(str(row.position)) or {}).get("source_hash")
            != novel_chapter_source_hash(row)
        )
    ]
    if invalid_extraction:
        raise HTTPException(
            status_code=409,
            detail=f"章节事实或记忆提取不完整: {invalid_extraction}",
        )
    if not is_state_gated_plan(revision.generation_plan) or is_v5_plan(
        revision.generation_plan
    ):
        return None
    eligible_ids: set[str] = set()
    invalid_candidates = []
    for row in chapters:
        entry = ledger_rows.get(str(row.position)) or {}
        events, memories = source_candidates(service.db, revision, row)
        actual = {
            "events": [item.business_id for item in events],
            "memories": [item.business_id for item in memories],
        }
        expected = {
            "events": list(entry.get("event_ids") or []),
            "memories": list(entry.get("memory_ids") or []),
        }
        if actual != expected:
            invalid_candidates.append(row.position)
        eligible_ids.update(actual["events"])
        eligible_ids.update(actual["memories"])
    if invalid_candidates:
        raise HTTPException(
            status_code=409,
            detail=f"章节候选证据或 ledger ID 不匹配: {invalid_candidates}",
        )
    return eligible_ids


def _require_current_report(revision, chapters) -> None:
    if revision.continuity_status != "passed":
        raise HTTPException(status_code=409, detail="连续性检查尚未通过")
    coverage = {
        item.get("business_id"): item.get("content_hash")
        for item in (revision.continuity_report or {}).get("coverage") or []
    }
    expected_coverage = {row.business_id: row.content_hash for row in chapters}
    if coverage != expected_coverage:
        raise HTTPException(status_code=409, detail="连续性报告未覆盖全部当前章节")
    if (
        is_v3_plan(revision.generation_plan)
        or is_v4_plan(revision.generation_plan)
        or is_v5_plan(revision.generation_plan)
    ):
        source_coverage = {
            item.get("business_id"): item.get("source_hash")
            for item in (revision.continuity_report or {}).get("coverage") or []
        }
        expected_sources = {
            row.business_id: novel_chapter_source_hash(row) for row in chapters
        }
        if source_coverage != expected_sources:
            raise HTTPException(
                status_code=409, detail="连续性报告未覆盖全部当前章节 source hash"
            )


def _promote_revision(service, revision, chapters, eligible_candidate_ids) -> None:
    story = revision.story
    retired = False
    if story.canonical_novel_export_id:
        previous = service.db.get(StoryNovelExport, story.canonical_novel_export_id)
        if previous and previous.id != revision.id:
            previous.lifecycle_status = "superseded"
            retired = retire_revision_candidates(
                service.db,
                story,
                {row.business_id for row in active_chapters(previous)},
            )
    revision.lifecycle_status = "approved"
    revision.approved_at = datetime.utcnow()
    revision.approved_by = service.user.id
    story.canonical_novel_export_id = revision.id
    candidates = CandidateService(NarrativeMemoryRepository(service.db))
    promoted = candidates.approve_source_candidates(
        story,
        valid_sources={
            row.business_id: novel_chapter_source_hash(row) for row in chapters
        },
        user_id=service.user.id,
        require_verified_evidence=is_state_gated_plan(revision.generation_plan),
        eligible_candidate_ids=eligible_candidate_ids,
        commit=False,
    )
    if retired and not promoted:
        candidates.refresh_ledger(story, commit=False)
    service.db.commit()
