"""V5 chain, chapter-quality, and report gates without legacy Canon state."""

from app.services.narrative_memory.source_hash import novel_chapter_source_hash
from fastapi import HTTPException

from .story_novel_canon_service import content_hash
from .story_novel_v5_plan import valid_v5_plan
from .story_novel_v5_invocation_gate import v5_invocation_issues
from .story_novel_v5_resume import validate_v5_chain


def require_v5_quality(db, revision, chapters, ledger_rows):
    plan = revision.generation_plan or {}
    if not valid_v5_plan(plan, revision.story_snapshot or {}):
        raise HTTPException(status_code=409, detail="V5 Schema/图/计划 hash 无效")
    invalid = []
    for chapter in chapters:
        entry = ledger_rows.get(str(chapter.position)) or {}
        issues = []
        if entry.get("status") != "ready" or entry.get("extraction_status") != "ready":
            issues.append("checkpoint")
        if entry.get("consistency_report", {}).get("status") != "passed":
            issues.append("consistency")
        if entry.get("readability_report", {}).get("status") != "passed":
            issues.append("readability")
        if entry.get("length_report", {}).get("status") != "passed":
            issues.append("length")
        if entry.get("plan_hash") != plan.get("plan_hash"):
            issues.append("plan_hash")
        if entry.get("schema_hash") != plan.get("consistency_schema_hash"):
            issues.append("schema_hash")
        if issues:
            invalid.append({"position": chapter.position, "issues": issues})
    if invalid:
        raise HTTPException(status_code=409, detail={"v5_chapter_gates": invalid})
    invocation_issues = v5_invocation_issues(db, revision, ledger_rows)
    if invocation_issues:
        raise HTTPException(
            status_code=409, detail={"v5_invocation_gates": invocation_issues}
        )
    final = validate_v5_chain(revision, plan["chapters"])
    current = (revision.continuity_ledger or {}).get("current_fact_graph") or {}
    if final["snapshot_hash"] != current.get("snapshot_hash"):
        raise HTTPException(
            status_code=409, detail="V5 current snapshot 与章节 hash 链不匹配"
        )


def build_v5_report(db, revision, chapters, ledger_rows):
    require_v5_quality(db, revision, chapters, ledger_rows)
    plan = revision.generation_plan or {}
    repaired = sum(
        bool((ledger_rows[str(row.position)]).get("repair_records")) for row in chapters
    )
    report = {
        "schema": "story_novel_continuity_review.v4",
        "status": "passed",
        "plan_version": plan.get("version"),
        "plan_hash": plan.get("plan_hash"),
        "consistency_schema_hash": plan.get("consistency_schema_hash"),
        "coverage": [
            {
                "business_id": row.business_id,
                "position": row.position,
                "content_hash": row.content_hash,
                "source_hash": novel_chapter_source_hash(row),
                "snapshot_after_hash": ledger_rows[str(row.position)].get(
                    "snapshot_after_hash"
                ),
            }
            for row in chapters
        ],
        "hard_metrics": {
            "state_chain_failed": 0,
            "readability_failed": 0,
            "length_failed": 0,
            "chapter_repair_rate": repaired / len(chapters) if chapters else 0,
        },
        "issues": [],
        "summary": "V5 动态 Schema、逐章状态补丁、证据、可读性与 hash 链均通过",
    }
    report["report_hash"] = content_hash(report)
    return report


def save_v5_report(service, revision, chapters, ledger_rows):
    if revision.lifecycle_status != "draft" or len(chapters) != int(
        revision.chapter_count or 0
    ):
        raise HTTPException(status_code=409, detail="V5 章节尚未完整生成")
    revision.continuity_report = build_v5_report(
        service.db, revision, chapters, ledger_rows
    )
    revision.continuity_status = "passed"
    service.db.commit()
    return revision.continuity_report
