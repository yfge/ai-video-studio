"""Payload and report builders for layered long-form continuity review."""

from app.services.narrative_memory.source_hash import novel_chapter_source_hash

from .story_novel_canon_service import content_hash
from .story_novel_continuity_grounding import contract_reference_catalog
from .story_novel_sentence_spans import (
    audit_sentence_index,
    sentence_index_hash,
    sentence_spans,
)


def window_payload(revision, chapters: list, ledger_rows: dict | None = None) -> dict:
    plan = revision.generation_plan or {}
    ledger_rows = ledger_rows or {}
    return {
        "story_contract": revision.story_snapshot or {},
        "compiled_canon": plan.get("canon") or {},
        "valid_contract_refs": sorted(contract_reference_catalog(revision, chapters)),
        "chapters": [
            {
                "business_id": row.business_id,
                "content_hash": row.content_hash,
                "position": row.position,
                "title": row.title,
                "sentence_index": audit_sentence_index(
                    sentence_spans(row.content_text or "")
                ),
                "sentence_index_hash": sentence_index_hash(
                    sentence_spans(row.content_text or "")
                ),
                "chapter_contract": next(
                    (
                        item
                        for item in plan.get("chapters") or []
                        if int(item["position"]) == row.position
                    ),
                    {},
                ),
                "checkpoint": {
                    key: value
                    for key, value in (ledger_rows.get(str(row.position)) or {}).items()
                    if key
                    in {
                        "body_hash",
                        "source_hash",
                        "brief_hash",
                        "expected_delta",
                        "proof_spans",
                        "state_before_hash",
                        "state_after_hash",
                        "future_audit",
                    }
                },
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
        "proof_spans": entry.get("proof_spans") or [],
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
        "valid_contract_refs": sorted(contract_reference_catalog(revision, chapters)),
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
                "source_hash": novel_chapter_source_hash(row),
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
        "blocking_issues": [
            str(item.get("message") or "")
            for item in issues
            if item.get("severity") == "blocking"
        ],
        "revision_priorities": global_report.get("revision_priorities") or [],
        "repair_groups": global_report.get("repair_groups") or [],
        "reviewer_model": (
            (plan.get("model_policy") or {}).get("audit_model") or revision.model
        ),
        "review_invocations": [
            report.get("invocation")
            for report in window_reports
            if report.get("invocation")
        ]
        + ([global_report["invocation"]] if global_report.get("invocation") else []),
        "canon_hash": plan.get("canon_hash"),
        "plan_version": plan.get("version"),
        "plan_hash": plan.get("plan_hash"),
    }
    report["report_hash"] = content_hash(report)
    return report
