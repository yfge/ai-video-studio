"""Payload and report builders for layered long-form continuity review."""

from app.services.narrative_memory.source_hash import novel_chapter_source_hash

from .story_novel_canon_service import content_hash


def window_payload(revision, chapters: list) -> dict:
    return {
        "story_contract": revision.story_snapshot or {},
        "chapters": [
            {
                "business_id": row.business_id,
                "content_hash": row.content_hash,
                "position": row.position,
                "title": row.title,
                "content": row.content_text,
            }
            for row in chapters
        ],
    }


def global_chapter_row(chapter, ledger_rows: dict) -> dict:
    entry = ledger_rows.get(str(chapter.position)) or {}
    return {
        "business_id": chapter.business_id,
        "content_hash": chapter.content_hash,
        "position": chapter.position,
        "title": chapter.title,
        "summary": chapter.summary,
        "cliffhanger": chapter.cliffhanger,
        "plot_delta": entry.get("plot_delta"),
        "state_delta": entry.get("state_delta"),
        "state_before_hash": entry.get("state_before_hash"),
        "state_after_hash": entry.get("state_after_hash"),
    }


def global_payload(
    revision,
    chapters: list,
    ledger_rows: dict,
    events: list,
    memories: list,
    window_reports: list,
) -> dict:
    plan = revision.generation_plan or {}
    return {
        "story_contract": revision.story_snapshot or {},
        "generation_plan": plan,
        "compiled_canon": plan.get("canon") or {},
        "chapters": [global_chapter_row(row, ledger_rows) for row in chapters],
        "facts": events,
        "character_memories": memories,
        "rolling_state": (revision.continuity_ledger or {}).get("current_state"),
        "window_findings": window_reports,
    }


def review_ready(chapters: list, ledger_rows: dict) -> bool:
    return all(
        (ledger_rows.get(str(row.position)) or {}).get("extraction_status") == "ready"
        and (ledger_rows.get(str(row.position)) or {}).get("source_hash")
        == novel_chapter_source_hash(row)
        for row in chapters
    )


def compile_report(
    revision,
    chapters: list,
    window_reports: list,
    global_report: dict,
    metrics: dict,
) -> dict:
    plan = revision.generation_plan or {}
    issues = [
        item for report in window_reports for item in report["issues"]
    ] + global_report["issues"]
    report = {
        "schema": "story_novel_continuity_review.v3",
        "summary": global_report["summary"],
        "coverage": [
            {
                "business_id": row.business_id,
                "content_hash": row.content_hash,
                "position": row.position,
            }
            for row in chapters
        ],
        "window_reports": window_reports,
        "review_batches": [
            {
                "batch_index": report.get("batch_index", index),
                "chapters": list(report.get("chapter_refs") or []),
            }
            for index, report in enumerate(window_reports, start=1)
        ],
        "issues": issues,
        "hard_metrics": metrics,
        "overall_score": global_report.get("overall_score"),
        "quality_scores": global_report.get("quality_scores") or {},
        "major_strengths": global_report.get("major_strengths") or [],
        "blocking_issues": global_report.get("blocking_issues") or [],
        "revision_priorities": global_report.get("revision_priorities") or [],
        "repair_groups": global_report.get("repair_groups") or [],
        "reviewer_model": revision.model,
        "canon_hash": plan.get("canon_hash"),
        "plan_version": plan.get("version"),
        "plan_hash": plan.get("plan_hash"),
    }
    report["report_hash"] = content_hash(report)
    return report
