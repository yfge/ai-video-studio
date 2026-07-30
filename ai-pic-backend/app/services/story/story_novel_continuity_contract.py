"""Prompt and output normalization for layered novel continuity review."""

from __future__ import annotations

import json

from app.utils.json_utils import extract_json_block
from fastapi import HTTPException

from .story_novel_continuity_grounding import ground_issue, normalize_repair_groups
from .story_novel_prompt_renderer import render_novel_prompt


def continuity_prompt(
    label: str, payload: dict, *, issue_limit: int, include_editorial: bool = False
) -> str:
    return render_novel_prompt(
        "story_novel_continuity_review_v3",
        label=label,
        payload_json=json.dumps(
            payload, ensure_ascii=False, separators=(",", ":"), default=str
        ),
        issue_limit=issue_limit,
        include_editorial=include_editorial,
    )


def normalize_continuity_report(
    text: str,
    prefix: str,
    *,
    include_editorial=False,
    evidence_catalog=None,
    contract_catalog=None,
    canon=None,
) -> dict:
    report = extract_json_block(text)
    if not report or not isinstance(report.get("issues"), list):
        raise HTTPException(status_code=500, detail="连续性检查返回格式无效")
    issues = []
    for index, raw in enumerate(report["issues"], start=1):
        item = dict(raw) if isinstance(raw, dict) else {"message": str(raw)}
        source_id = str(item.get("id") or index)
        item["id"] = f"{prefix}-{source_id}"
        item["severity"] = (
            "blocking" if item.get("severity") == "blocking" else "warning"
        )
        item["chapter_business_ids"] = list(item.get("chapter_business_ids") or [])
        issues.append(
            ground_issue(item, evidence_catalog or {}, set(contract_catalog or []))
        )
    result = {"summary": str(report.get("summary") or ""), "issues": issues}
    if include_editorial:
        result["overall_score"] = _normalize_overall_score(report.get("overall_score"))
        result["quality_scores"] = _normalize_scores(report.get("quality_scores"))
        result["major_strengths"] = _normalize_strings(report.get("major_strengths"))
        result["blocking_issues"] = [
            str(item.get("message") or "")
            for item in issues
            if item["severity"] == "blocking"
        ]
        result["revision_priorities"] = _normalize_priorities(
            report.get("revision_priorities")
        )
        result["repair_groups"] = normalize_repair_groups(
            report.get("repair_groups"), prefix, issues, canon or {}
        )
    return result


def _normalize_overall_score(raw) -> float | None:
    if raw is None:
        return None
    try:
        return min(100.0, max(0.0, float(raw)))
    except (TypeError, ValueError):
        return None


def _normalize_strings(raw) -> list[str]:
    if not isinstance(raw, list):
        return []
    return [str(value) for value in raw if str(value).strip()]


def _normalize_priorities(raw) -> list[dict]:
    result = []
    for item in raw or []:
        if not isinstance(item, dict):
            continue
        priority = str(item.get("priority") or "").strip()
        items = _normalize_strings(item.get("items"))
        if priority and items:
            result.append({"priority": priority, "items": items})
    return result


def _normalize_scores(raw) -> dict:
    result = {}
    for key in (
        "structure",
        "character",
        "prose",
        "world",
        "emotion",
        "originality",
        "adaptation",
        "progression",
        "reader_appeal",
    ):
        item = (raw or {}).get(key) if isinstance(raw, dict) else None
        if not isinstance(item, dict):
            continue
        result[key] = {
            "score": min(10.0, max(0.0, float(item.get("score") or 0))),
            "rationale": str(item.get("rationale") or ""),
        }
    return result
