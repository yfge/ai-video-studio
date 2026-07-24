"""Prompt and output normalization for layered novel continuity review."""

from __future__ import annotations

import json

from app.utils.json_utils import extract_json_block
from fastapi import HTTPException


def continuity_prompt(
    label: str, payload: dict, *, issue_limit: int, include_editorial: bool = False
) -> str:
    output_shape = (
        """{"summary":"结论","issues":[{"id":"stable-id","severity":"blocking|warning",
"chapter_business_ids":["id"],"message":"问题","suggestion":"修复建议"}],
"overall_score":0,"quality_scores":{},"major_strengths":[],"blocking_issues":[],
"revision_priorities":[{"priority":"P0","items":[]}],"repair_groups":[]}"""
        if include_editorial
        else """{"summary":"结论","issues":[{"id":"stable-id",
"severity":"blocking|warning","chapter_business_ids":["id"],"message":"问题",
"suggestion":"修复建议"}]}"""
    )
    editorial = (
        """
全局检查还必须输出：
"overall_score"：0–100 的独立编辑判断，不得由分项分数加权或平均计算。
"quality_scores"：structure、character、prose、world、emotion、originality、
adaptation 七项，每项含 0–10 score 和一句 rationale；不要计算总分。
"major_strengths"：主要优点字符串列表。
"blocking_issues"：blocking 问题的简明字符串列表；每项还必须出现在 issues
且 severity=blocking。
"revision_priorities"：按 P0、P1、P2、P3 排列，每项含 priority 和 items。
"repair_groups"：把同一 Canon 冲突分组，包含 id、title、issue_ids、
canon_target(section/item_id/field)、suggested_value、affected_chapter_business_ids、
earliest_position。canon_target 必须引用输入 Canon 中已有项目；无法定位则不要生成修复组。
本轮验收参考阈值字段：overall_score >= 75，quality_scores 的 structure、
character、world 均 >= 7，blocking_issues 为空。阈值只用于验收记录，不得据此
输出审批结论或自动批准。"""
        if include_editorial
        else ""
    )
    return f"""你是中文长篇小说连续性审校员。检查时间、地点、角色知识、关系、能力、
世界规则、因果、伏笔、重复情节、角色弧与节奏。{label}
输入：{json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)}
issues 最多 {issue_limit} 条，只保留可执行且不重复的问题；summary、message、suggestion
都必须简洁，每项 message 和 suggestion 各不超过 160 个中文字符。
{editorial}
只输出严格 JSON：
{output_shape}
只有破坏叙事或后续改编的矛盾才标 blocking。"""


def normalize_continuity_report(
    text: str, prefix: str, *, include_editorial=False
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
        issues.append(item)
    result = {"summary": str(report.get("summary") or ""), "issues": issues}
    if include_editorial:
        reported_blockers = _normalize_strings(report.get("blocking_issues"))
        known_blockers = {
            str(item.get("message") or "")
            for item in issues
            if item["severity"] == "blocking"
        }
        for message in reported_blockers:
            if message not in known_blockers:
                issues.append(
                    {
                        "id": f"{prefix}-reported-blocker-{len(issues) + 1}",
                        "severity": "blocking",
                        "chapter_business_ids": [],
                        "message": message,
                    }
                )
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
        result["repair_groups"] = _normalize_repairs(
            report.get("repair_groups"), prefix
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
    ):
        item = (raw or {}).get(key) if isinstance(raw, dict) else None
        if not isinstance(item, dict):
            continue
        result[key] = {
            "score": min(10.0, max(0.0, float(item.get("score") or 0))),
            "rationale": str(item.get("rationale") or ""),
        }
    return result


def _normalize_repairs(raw, prefix: str) -> list[dict]:
    allowed = {
        "timeline",
        "entities",
        "world_rules",
        "milestones",
        "character_arcs",
        "initial_state",
    }
    result = []
    for index, item in enumerate(raw or [], start=1):
        if not isinstance(item, dict):
            continue
        target = item.get("canon_target") or {}
        if target.get("section") not in allowed:
            continue
        issue_ids = [
            value if str(value).startswith(f"{prefix}-") else f"{prefix}-{value}"
            for value in item.get("issue_ids") or []
        ]
        result.append(
            {
                **item,
                "id": f"{prefix}-repair-{item.get('id') or index}",
                "issue_ids": issue_ids,
            }
        )
    return result
