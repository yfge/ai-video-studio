"""Redact future details while deciding whether prior prose is safe to reuse."""

from __future__ import annotations

import json
import re


def fixed_date_repair_action(violations: list[dict]) -> str:
    dates = []
    for item in violations:
        message = str(item.get("message") or "")
        dates.extend(re.findall(r"正文缺少当前事件固定日期: ([^；]+)", message))
        dates.extend(
            re.findall(
                r"(?:时间线证据缺少固定日期|正文缺少固定日期) " r"([^:；]+): [^；]+",
                message,
            )
        )
    dates = list(dict.fromkeys(dates))
    if not dates:
        return ""
    encoded = json.dumps(dates, ensure_ascii=False, separators=(",", ":"))
    return (
        "最终固定日期 checklist：逐句检查所有涉及当前 key_event "
        "或 immutable timeline 的日期，"
        f"必须逐字使用 {encoded}；"
        "正文首段第一句先写 checklist 中最早日期；每个日期必须在对应事件发生前或同一句开头出现；"
        "事后补写不算，不得用相邻日期、次日或 Story 全局结束日替代。"
    )


def repair_guidance(
    violations: list[dict],
    *,
    current_event_ids: list[str] | None = None,
    current_timeline_ids: list[str] | None = None,
) -> list[dict]:
    """Keep current-contract fixes while removing future IDs and values."""
    labels = {
        "canon_violation": "正文只可完成当前章合同，并须完整呈现当前计划事件与伏笔变化",
        "state_reversion": "保持当前状态，不得回滚人物、物件、关系或权限",
        "duplicate_milestone": "不得重复已经完成的一次性里程碑",
        "illegal_knowledge": "角色只能通过当前章合同允许的来源获得知识",
        "unexplained_location": (
            "只允许当前章 location_transitions 中的地点移动；"
            "清单为空时删除全部移动并保持 current_state 地点"
        ),
    }
    guidance = []
    seen = set()
    for item in violations:
        code = str(item.get("code") or "canon_violation")
        events = set(current_event_ids or [])
        timeline = set(current_timeline_ids or [])
        for message in _guidance_parts(
            str(item.get("message") or ""),
            current_event_ids=events,
            current_timeline_ids=timeline,
        ):
            if not _safe_repair_message(
                message,
                current_event_ids=events,
                current_timeline_ids=timeline,
            ):
                message = labels.get(code, labels["canon_violation"])
            key = (code, message)
            if key not in seen:
                guidance.append({"code": code, "message": message})
                seen.add(key)
    return guidance


def _guidance_parts(
    message: str,
    *,
    current_event_ids: set[str],
    current_timeline_ids: set[str],
) -> list[str]:
    """Split mixed extraction failures so safe current fixes survive redaction."""
    prefix = "章节状态提取失败: "
    if not message.startswith(prefix):
        return [message]
    details = message.removeprefix(prefix).split("；")
    if not details or all(
        _safe_repair_message(
            detail,
            current_event_ids=current_event_ids,
            current_timeline_ids=current_timeline_ids,
        )
        for detail in details
    ):
        return [message]
    return details


def can_reuse_prior_result(
    violations: list[dict],
    *,
    current_event_ids: list[str] | None = None,
    current_timeline_ids: list[str] | None = None,
) -> bool:
    """Keep safe prose unless a failure proves it contains future information."""
    events = set(current_event_ids or [])
    timeline = set(current_timeline_ids or [])
    return bool(violations) and not any(
        _future_sensitive_message(
            str(item.get("message") or ""),
            current_event_ids=events,
            current_timeline_ids=timeline,
        )
        for item in violations
    )


def select_repair_evaluation(first: dict, repair: dict) -> dict:
    """Never replace parseable prose unless repair strictly reduces failures."""
    if repair.get("passed") or not first.get("result"):
        return repair
    first_violations = _normalized_violations(first)
    repair_violations = _normalized_violations(repair)
    return repair if repair_violations < first_violations else first


def _normalized_violations(evaluation: dict) -> set[tuple[str, str]]:
    return {
        (
            str(item.get("code") or "canon_violation").strip(),
            str(item.get("message") or "").strip(),
        )
        for item in (evaluation.get("state_validation") or {}).get("violations") or []
    }


def _future_sensitive_message(
    message: str,
    *,
    current_event_ids: set[str],
    current_timeline_ids: set[str],
) -> bool:
    extraction_prefix = "章节状态提取失败: "
    if message.startswith(extraction_prefix):
        return any(
            _future_sensitive_message(
                detail,
                current_event_ids=current_event_ids,
                current_timeline_ids=current_timeline_ids,
            )
            for detail in message.removeprefix(extraction_prefix).split("；")
        )
    explicit_future_markers = (
        "正文提前完成未来事件:",
        "正文提前出现计划第 ",
        "提前消费里程碑:",
        "正文提前打开未规划伏笔:",
        "正文提前回收未来伏笔:",
        "正文出现未规划事件:",
        "正文引入未授权具名角色:",
        "状态提前包含未来里程碑结果:",
    )
    if any(marker in message for marker in explicit_future_markers):
        return True
    for prefix in ("正文缺少计划事件: ", "事件缺少可核对的正文证据: "):
        if message.startswith(prefix):
            return message.removeprefix(prefix) not in current_event_ids
    for prefix in ("时间线缺少正文证据: ",):
        if message.startswith(prefix):
            return message.removeprefix(prefix) not in current_timeline_ids
    if (
        message.startswith("时间线证据缺少固定日期 ")
        or message.startswith("正文缺少固定日期 ")
    ) and ": " in message:
        return message.rsplit(": ", 1)[-1] not in current_timeline_ids
    return False


def _safe_repair_message(
    message: str,
    *,
    current_event_ids: set[str],
    current_timeline_ids: set[str],
) -> bool:
    extraction_prefix = "章节状态提取失败: "
    if message.startswith(extraction_prefix):
        details = message.removeprefix(extraction_prefix).split("；")
        return bool(details) and all(
            _safe_repair_message(
                detail,
                current_event_ids=current_event_ids,
                current_timeline_ids=current_timeline_ids,
            )
            for detail in details
        )
    if message in {
        "missing JSON object",
        "正文不得自报角色状态；状态只由独立 typed audit 写入",
        "正文时间证据必须逐项等于当前章节 immutable timeline",
    }:
        return True
    if re.fullmatch(r"章节长度为 \d+，要求 \d+–\d+", message):
        return True
    if re.fullmatch(
        r"正文自报(?:本章事件|新开伏笔|回收伏笔)必须逐项等于当前章节合同",
        message,
    ):
        return True
    if message.startswith("正文违反 Canon 世界规则 "):
        return True
    for prefix in ("正文缺少计划事件: ", "事件缺少可核对的正文证据: "):
        if message.startswith(prefix):
            return message.removeprefix(prefix) in current_event_ids
    for prefix in ("时间线缺少正文证据: ",):
        if message.startswith(prefix):
            return message.removeprefix(prefix) in current_timeline_ids
    if message.startswith("时间线证据缺少固定日期 ") and ": " in message:
        return message.rsplit(": ", 1)[-1] in current_timeline_ids
    if message.startswith("正文缺少固定日期 ") and ": " in message:
        return message.rsplit(": ", 1)[-1] in current_timeline_ids
    return message.startswith("正文缺少当前事件固定日期: ")
