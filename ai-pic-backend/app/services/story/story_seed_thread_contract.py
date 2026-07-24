"""Deterministic StorySeed thread-opening and later-payoff contract."""

from __future__ import annotations

MAX_PAYOFFS_PER_CHAPTER = 3


def payoff_evidence_prefix(thread_id: str) -> str:
    return f"关于“{thread_id}”的最终证据确认："


def payoff_evidence_sources(data: dict, thread_ids: list[str]) -> dict[str, str]:
    return {
        row["thread_id"]: row["evidence_key_event"]
        for row in data.get("thread_payoffs") or []
        if row["thread_id"] in thread_ids
        and isinstance(row.get("evidence_key_event"), str)
        and row["evidence_key_event"].strip()
        and row["evidence_key_event"].startswith(
            payoff_evidence_prefix(row["thread_id"])
        )
    }


def merge_payoff_evidence(outline):
    data = outline.model_dump()
    chapters = {
        int(chapter["position"]): chapter for chapter in data.get("chapters") or []
    }
    for row in data.get("thread_payoffs") or []:
        chapter = chapters.get(row.get("payoff_position"))
        evidence = row.get("evidence_key_event")
        prefix = payoff_evidence_prefix(row.get("thread_id"))
        normalized = evidence if evidence.startswith(prefix) else f"{prefix}{evidence}"
        row["evidence_key_event"] = normalized
        if chapter is None:
            continue
        if normalized not in chapter["key_events"]:
            chapter["key_events"].append(normalized)
    return type(outline).model_validate(data)


def validate_seed_thread_contract(
    outline,
    *,
    require_version: bool = False,
) -> list[dict]:
    data = (
        outline.model_dump() if hasattr(outline, "model_dump") else dict(outline or {})
    )
    version = int(data.get("thread_schedule_version") or 0)
    rows = list(data.get("thread_payoffs") or [])
    chapters = list(data.get("chapters") or [])
    if version != 1:
        if require_version:
            raise ValueError("结构化大纲缺少 thread_schedule_version=1 伏笔回收合同")
        if rows:
            raise ValueError("旧版结构化大纲不得携带 thread_payoffs")
        return []

    opened = _opened_threads(chapters)
    events = {
        int(chapter.get("position") or 0): list(chapter.get("key_events") or [])
        for chapter in chapters
    }
    seen: dict[str, dict] = {}
    counts: dict[int, int] = {}
    errors: list[str] = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict) or set(row) != {
            "thread_id",
            "payoff_position",
            "evidence_key_event",
        }:
            errors.append(f"第 {index} 条 thread_payoff 字段无效")
            continue
        thread_id = row["thread_id"]
        payoff = row["payoff_position"]
        evidence = row["evidence_key_event"]
        if not isinstance(thread_id, str) or not thread_id:
            errors.append(f"第 {index} 条 thread_id 必须是非空字符串")
            continue
        if thread_id not in opened:
            errors.append(f"thread_payoffs 引用未知伏笔: {thread_id}")
            continue
        if thread_id in seen:
            errors.append(f"伏笔重复回收: {thread_id}")
        else:
            seen[thread_id] = row
        if type(payoff) is not int or payoff not in events:
            errors.append(f"伏笔 {thread_id} 的 payoff_position 无效: {payoff!r}")
            continue
        counts[payoff] = counts.get(payoff, 0) + 1
        if payoff <= opened[thread_id]:
            errors.append(
                f"伏笔必须在更晚章节回收: {thread_id} "
                f"(open={opened[thread_id]}, payoff={payoff})"
            )
        if not isinstance(evidence, str) or evidence not in events[payoff]:
            errors.append(
                f"第 {payoff} 章 evidence_key_event 未逐字复制: "
                f"{thread_id}={evidence!r}"
            )
        locations = [
            position
            for position, chapter_events in events.items()
            for event in chapter_events
            if event == evidence
        ]
        if locations != [payoff]:
            errors.append(
                f"伏笔 {thread_id} 的回收证据必须全书唯一且只位于第 "
                f"{payoff} 章，实际位于 {locations}"
            )
        prefix = payoff_evidence_prefix(thread_id)
        if (
            not isinstance(evidence, str)
            or not evidence.startswith(prefix)
            or (len(evidence) <= len(prefix))
        ):
            errors.append(f"伏笔 {thread_id} 的回收事件必须使用显式问题标签并给出答案")
    missing = [thread_id for thread_id in opened if thread_id not in seen]
    if missing:
        errors.append(f"伏笔回收合同遗漏: {missing}")
    for position, count in counts.items():
        if count > MAX_PAYOFFS_PER_CHAPTER:
            errors.append(
                f"第 {position} 章集中回收 {count} 条伏笔，"
                f"超过单章上限 {MAX_PAYOFFS_PER_CHAPTER}"
            )
    if errors:
        raise ValueError("；".join(dict.fromkeys(errors)))
    return [seen[thread_id] for thread_id in opened]


def outline_has_open_threads(outline) -> bool:
    data = (
        outline.model_dump() if hasattr(outline, "model_dump") else dict(outline or {})
    )
    return any(chapter.get("open_threads") for chapter in data.get("chapters") or [])


def _opened_threads(chapters: list[dict]) -> dict[str, int]:
    opened: dict[str, int] = {}
    for chapter in chapters:
        position = int(chapter.get("position") or 0)
        for thread_id in chapter.get("open_threads") or []:
            if not isinstance(thread_id, str) or not thread_id:
                raise ValueError(f"第 {position} 章伏笔 ID 必须是非空字符串")
            if any(marker in thread_id for marker in ("；", ";", "、", "以及")):
                raise ValueError(f"伏笔 ID 必须只表达一个原子问题: {thread_id}")
            if thread_id in opened:
                raise ValueError(f"结构化大纲伏笔 ID 重复: {thread_id}")
            opened[thread_id] = position
    return opened
