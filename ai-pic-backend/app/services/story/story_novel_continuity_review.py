"""Payload and report builders for layered long-form continuity review."""

from app.services.narrative_memory.source_hash import novel_chapter_source_hash

from .story_novel_canon_service import content_hash
from .story_novel_context_utils import frozen_story_contract
from .story_novel_continuity_global_context import build_global_context
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
        "story_contract": frozen_story_contract(revision.story_snapshot or {}),
        "authority_order": [
            "compiled_canon",
            "validated_chapter_contract",
            "validated_checkpoint",
            "story_contract",
        ],
        "state_chain_contract": {
            "state_before": "章节开始前的已验证状态，不是本章结束状态",
            "state_delta": "本章正文允许且已经验证的实际状态变化",
            "state_after": "应用本章 state_delta 后的已验证状态",
            "window_entry_state": "窗口开始前一章的相关主体状态",
            "window_scope": "窗口外的状态变化由连续 hash 链证明，不得因正文未重演而判为缺失",
        },
        "window_entry_state": _window_entry_state(plan, chapters, ledger_rows),
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
                        "state_delta",
                        "state_validation",
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


def _window_entry_state(plan: dict, chapters: list, ledger_rows: dict) -> dict:
    first_position = min((row.position for row in chapters), default=1)
    if first_position <= 1:
        return {}
    prior = ledger_rows.get(str(first_position - 1)) or {}
    subjects = (prior.get("state_after") or {}).get("subjects") or {}
    relevant_ids = _window_subject_ids(plan, {row.position for row in chapters})
    return {
        "source_position": first_position - 1,
        "state_after_hash": prior.get("state_after_hash"),
        "subjects": {
            subject_id: subjects[subject_id]
            for subject_id in sorted(relevant_ids)
            if subject_id in subjects
        },
    }


def _window_subject_ids(plan: dict, positions: set[int]) -> set[str]:
    result = set()
    for chapter in plan.get("chapters") or []:
        if int(chapter.get("position") or 0) not in positions:
            continue
        for key in ("preconditions", "state_transitions", "location_transitions"):
            result.update(
                str(item["subject_id"])
                for item in chapter.get(key) or []
                if item.get("subject_id")
            )
    return result


def global_payload(
    revision,
    chapters: list,
    ledger_rows: dict,
    events: list,
    memories: list,
    window_reports: list,
) -> dict:
    return build_global_context(
        revision,
        chapters,
        ledger_rows,
        events,
        memories,
        window_reports,
        sorted(contract_reference_catalog(revision, chapters)),
    )


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
    reviewer_model: str | None = None,
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
        "global_context_budget": global_report.get("context_budget") or {},
        "repair_groups": global_report.get("repair_groups") or [],
        "reviewer_model": (
            reviewer_model
            or (plan.get("model_policy") or {}).get("audit_model")
            or revision.model
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
