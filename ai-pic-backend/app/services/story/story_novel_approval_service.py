"""Approval boundary for a complete long-form novel revision."""

from datetime import datetime

from app.models.story_novel_export import StoryNovelExport
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.services.narrative_memory.candidate_service import CandidateService
from app.services.narrative_memory.source_hash import novel_chapter_source_hash
from fastapi import HTTPException

from .story_novel_candidate_refresh import retire_revision_candidates
from .story_novel_canon_service import (
    CANON_GATE_VERSION,
    content_hash,
    normalize_canon,
    validate_generation_plan,
)
from .story_novel_chapter_gate import chapter_length_range
from .story_novel_chapter_service import non_whitespace_chars, source_candidates
from .story_novel_continuity_service import require_valid_state_chain
from .story_novel_domain import active_chapters
from .story_novel_length_service import generation_plan_hash
from .story_novel_state_service import REQUIRED_HARD_METRICS


def approve_revision(service, revision):
    chapters = _require_complete_chapters(revision)
    plan = dict(revision.generation_plan or {})
    ledger_rows = (revision.continuity_ledger or {}).get("chapters") or {}
    _require_lengths(chapters, plan)
    eligible_candidate_ids = _require_extraction(
        service, revision, chapters, ledger_rows
    )
    if plan.get("schema") == "story_novel_generation_plan.v2":
        _require_current_frozen_plan(revision, plan)
        _require_v2_quality(revision, chapters, ledger_rows)
    _require_current_report(revision, chapters)
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
    if (revision.generation_plan or {}).get(
        "schema"
    ) != "story_novel_generation_plan.v2":
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
        require_verified_evidence=(revision.generation_plan or {}).get("schema")
        == "story_novel_generation_plan.v2",
        eligible_candidate_ids=eligible_candidate_ids,
        commit=False,
    )
    if retired and not promoted:
        candidates.refresh_ledger(story, commit=False)
    service.db.commit()


def _require_current_frozen_plan(revision, plan: dict) -> None:
    snapshot = revision.story_snapshot or {}
    outline = (snapshot.get("story_seed") or {}).get("structured_outline") or {}
    if plan.get("status") != "ready":
        raise HTTPException(status_code=409, detail="生成计划尚未就绪")
    if int(plan.get("story_seed_version") or 0) != int(
        snapshot.get("story_seed_version") or 0
    ):
        raise HTTPException(status_code=409, detail="冻结 StorySeed 版本不匹配")
    if plan.get("outline_hash") != content_hash(outline):
        raise HTTPException(status_code=409, detail="冻结大纲 hash 已变化")
    try:
        canon = normalize_canon(
            plan.get("canon") or {},
            required_gate_version=CANON_GATE_VERSION,
        )
        validate_generation_plan(canon, plan.get("chapters") or [])
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=409, detail=f"Canon/章节合同门禁无效: {exc}"
        ) from exc
    if (
        int(plan.get("canon_gate_version") or 0) != CANON_GATE_VERSION
        or plan.get("canon_hash") != canon["canon_hash"]
        or plan.get("plan_hash") != generation_plan_hash(plan)
    ):
        raise HTTPException(status_code=409, detail="Canon 或生成计划 hash 不匹配")
    positions = [int(item.get("position") or 0) for item in plan.get("chapters") or []]
    if positions != list(range(1, len(positions) + 1)):
        raise HTTPException(status_code=409, detail="冻结章节计划不连续")
    report = revision.continuity_report or {}
    if (
        report.get("status") == "stale"
        or report.get("plan_version") != plan.get("version")
        or report.get("plan_hash") != plan.get("plan_hash")
    ):
        raise HTTPException(status_code=409, detail="连续性报告未绑定当前生成计划")


def _require_v2_quality(revision, chapters, ledger_rows) -> None:
    canon_hash = (revision.generation_plan or {}).get("canon_hash")
    invalid_state = [
        row.position
        for row in chapters
        if (
            (ledger_rows.get(str(row.position)) or {}).get("status") != "ready"
            or (ledger_rows.get(str(row.position)) or {}).get("canon_hash")
            != canon_hash
            or (
                (ledger_rows.get(str(row.position)) or {}).get("state_validation") or {}
            ).get("status")
            != "passed"
        )
    ]
    if invalid_state:
        raise HTTPException(
            status_code=409, detail=f"章节状态门禁不完整: {invalid_state}"
        )
    require_valid_state_chain(revision, chapters, ledger_rows)
    report = dict(revision.continuity_report or {})
    if (
        report.get("schema") != "story_novel_continuity_review.v3"
        or report.get("canon_hash") != canon_hash
    ):
        raise HTTPException(status_code=409, detail="连续性报告未使用当前 Canon")
    expected_hash = report.pop("report_hash", None)
    if not expected_hash or expected_hash != content_hash(report):
        raise HTTPException(status_code=409, detail="连续性报告 hash 不匹配")
    hard_metrics = report.get("hard_metrics") or {}
    missing_metrics = REQUIRED_HARD_METRICS - set(hard_metrics)
    if missing_metrics:
        raise HTTPException(
            status_code=409,
            detail=f"确定性质量门禁不完整: {sorted(missing_metrics)}",
        )
    failed = {
        key: value
        for key, value in hard_metrics.items()
        if key != "chapter_repair_rate" and value
    }
    if failed:
        raise HTTPException(status_code=409, detail=f"确定性质量门禁未通过: {failed}")
