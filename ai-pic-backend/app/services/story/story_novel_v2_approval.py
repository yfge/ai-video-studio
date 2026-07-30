"""State-gated v2 approval checks kept separate from the v3 quality contract."""

from fastapi import HTTPException

from .story_novel_canon_service import content_hash
from .story_novel_continuity_service import require_valid_state_chain
from .story_novel_state_service import REQUIRED_HARD_METRICS


def require_v2_quality(revision, chapters, ledger_rows) -> None:
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
