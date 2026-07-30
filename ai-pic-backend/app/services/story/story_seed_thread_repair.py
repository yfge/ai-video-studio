"""One-shot provider repair for an otherwise valid StorySeed thread contract."""

from __future__ import annotations

from app.schemas.story_seed import StorySeedStructuredOutline
from app.utils.json_utils import extract_json_block

from .story_novel_canon_service import canonical_json
from .story_novel_prompt_renderer import render_novel_prompt
from .story_seed_thread_contract import (
    MAX_PAYOFFS_PER_CHAPTER,
    payoff_evidence_sources,
    validate_seed_thread_contract,
)


def repair_conflict_ids(outline: StorySeedStructuredOutline) -> list[str]:
    data = outline.model_dump()
    opened = _opened_threads(data["chapters"])
    rows = list(data.get("thread_payoffs") or [])
    conflicts: set[str] = set()
    seen: set[str] = set()
    valid_rows: list[dict] = []
    unknown = False
    if int(data.get("thread_schedule_version") or 0) != 1:
        conflicts.update(opened)
    events = {
        int(chapter["position"]): list(chapter.get("key_events") or [])
        for chapter in data["chapters"]
    }
    for row in rows:
        thread_id = row.get("thread_id")
        if thread_id not in opened:
            unknown = True
            continue
        if thread_id in seen:
            conflicts.add(thread_id)
        seen.add(thread_id)
        payoff = row.get("payoff_position")
        evidence = row.get("evidence_key_event")
        if (
            type(payoff) is not int
            or payoff not in events
            or payoff <= opened[thread_id]
            or evidence not in events[payoff]
        ):
            conflicts.add(thread_id)
        valid_rows.append(row)
    conflicts.update(set(opened) - seen)
    if unknown:
        conflicts.update(opened)
    by_position: dict[int, list[str]] = {}
    for row in valid_rows:
        thread_id = row["thread_id"]
        if thread_id in conflicts:
            continue
        by_position.setdefault(row["payoff_position"], []).append(thread_id)
    for thread_ids in by_position.values():
        conflicts.update(thread_ids[MAX_PAYOFFS_PER_CHAPTER:])
    return [thread_id for thread_id in opened if thread_id in conflicts]


def seed_thread_repair_prompt(
    outline: StorySeedStructuredOutline,
    conflict_ids: list[str],
    error: str | None = None,
) -> str:
    data = outline.model_dump()
    opened = _opened_threads(data["chapters"])
    preserved = _preserved_rows(data, set(conflict_ids), opened)
    occupied: dict[int, int] = {}
    for row in preserved.values():
        position = int(row["payoff_position"])
        occupied[position] = occupied.get(position, 0) + 1
    sources = payoff_evidence_sources(data, conflict_ids)
    if len(sources) != len(conflict_ids):
        raise ValueError("定向伏笔修复缺少初次结构模型的权威证据")
    assigned = _assigned_positions(data, conflict_ids, opened, occupied)
    chapters = {int(row["position"]): row for row in data["chapters"]}
    template = {
        "thread_payoff_repairs": [
            {
                "thread_id": thread_id,
                "payoff_position": assigned[thread_id],
                "evidence_key_event": sources[thread_id],
            }
            for thread_id in conflict_ids
        ]
    }
    context = {
        "authoritative_conflict_thread_ids": conflict_ids,
        "conflicts": [
            {
                "thread_id": thread_id,
                "open_position": opened[thread_id],
                "authoritative_source_evidence": sources[thread_id],
                "assigned_payoff_position": assigned[thread_id],
                "target_chapter": {
                    "position": assigned[thread_id],
                    "title": chapters[assigned[thread_id]]["title"],
                    "current_key_events": chapters[assigned[thread_id]]["key_events"],
                },
            }
            for thread_id in conflict_ids
        ],
    }
    return render_novel_prompt(
        "story_novel_seed_thread_repair_v3",
        max_payoffs_per_chapter=MAX_PAYOFFS_PER_CHAPTER,
        repair_template_json=canonical_json(template),
        repair_context_json=canonical_json(context),
        validation_error=error or "伏笔合同无效",
    )


def apply_seed_thread_repairs(
    outline: StorySeedStructuredOutline,
    repair_text: str,
    conflict_ids: list[str],
) -> StorySeedStructuredOutline:
    payload = extract_json_block(repair_text)
    repairs = (
        payload.get("thread_payoff_repairs") if isinstance(payload, dict) else None
    )
    if not isinstance(payload, dict) or set(payload) != {"thread_payoff_repairs"}:
        raise ValueError("伏笔修复必须只返回 thread_payoff_repairs JSON")
    if not isinstance(repairs, list):
        raise ValueError("thread_payoff_repairs 必须是数组")
    ids = [row.get("thread_id") if isinstance(row, dict) else None for row in repairs]
    if ids != conflict_ids or len(set(ids)) != len(ids):
        raise ValueError("伏笔修复必须按顺序逐项且仅覆盖全部冲突 thread_id")

    data = outline.model_dump()
    opened = _opened_threads(data["chapters"])
    preserved = _preserved_rows(data, set(conflict_ids), opened)
    chapters = {int(row["position"]): row for row in data["chapters"]}
    counts: dict[int, int] = {}
    for row in preserved.values():
        position = int(row["payoff_position"])
        counts[position] = counts.get(position, 0) + 1
    sources = payoff_evidence_sources(data, conflict_ids)
    assigned = _assigned_positions(data, conflict_ids, opened, counts)
    repaired: dict[str, dict] = {}
    for row in repairs:
        if set(row) != {"thread_id", "payoff_position", "evidence_key_event"}:
            raise ValueError("每条伏笔修复必须只有三个合同字段")
        thread_id = row["thread_id"]
        payoff = row["payoff_position"]
        evidence = row["evidence_key_event"]
        if type(payoff) is not int or payoff != assigned[thread_id]:
            raise ValueError(f"伏笔 {thread_id} 未使用系统预留的修复章节")
        if not isinstance(evidence, str) or not evidence.strip():
            raise ValueError(f"伏笔 {thread_id} 缺少有效 evidence_key_event")
        expected = sources[thread_id]
        if evidence != expected:
            raise ValueError(f"伏笔 {thread_id} 的修复事件加入了未授权事实")
        counts[payoff] = counts.get(payoff, 0) + 1
        if counts[payoff] > MAX_PAYOFFS_PER_CHAPTER:
            raise ValueError(f"第 {payoff} 章伏笔回收超过上限")
        for chapter in chapters.values():
            chapter["key_events"] = [
                event for event in chapter["key_events"] if event != evidence
            ]
        chapters[payoff]["key_events"].append(evidence)
        repaired[thread_id] = {
            "thread_id": thread_id,
            "payoff_position": payoff,
            "evidence_key_event": evidence,
        }
    data["thread_schedule_version"] = 1
    data["thread_payoffs"] = [
        repaired.get(thread_id) or preserved[thread_id] for thread_id in opened
    ]
    result = StorySeedStructuredOutline.model_validate(data)
    validate_seed_thread_contract(result, require_version=True)
    return result


def _preserved_rows(data: dict, conflicts: set[str], opened: dict[str, int]) -> dict:
    return {
        row["thread_id"]: row
        for row in data.get("thread_payoffs") or []
        if row["thread_id"] in opened and row["thread_id"] not in conflicts
    }


def _assigned_positions(
    data: dict,
    conflict_ids: list[str],
    opened: dict[str, int],
    occupied: dict[int, int],
) -> dict[str, int]:
    counts = dict(occupied)
    positions = [int(row["position"]) for row in data["chapters"]]
    previous = {
        row["thread_id"]: row.get("payoff_position")
        for row in data.get("thread_payoffs") or []
        if row["thread_id"] in conflict_ids
    }
    assigned: dict[str, int] = {}
    order = {thread_id: index for index, thread_id in enumerate(conflict_ids)}
    for thread_id in sorted(
        conflict_ids, key=lambda item: (-opened[item], order[item])
    ):
        preferred = previous.get(thread_id)
        if type(preferred) is not int or preferred <= opened[thread_id]:
            preferred = opened[thread_id] + 1
        candidates = [
            position
            for position in positions
            if position > opened[thread_id]
            and position >= preferred
            and counts.get(position, 0) < MAX_PAYOFFS_PER_CHAPTER
        ]
        if not candidates:
            raise ValueError(f"伏笔 {thread_id} 原回收章之后没有可用回收章节")
        position = min(
            candidates,
            key=lambda item: (abs(item - preferred), item),
        )
        assigned[thread_id] = position
        counts[position] = counts.get(position, 0) + 1
    return assigned


def _opened_threads(chapters: list[dict]) -> dict[str, int]:
    opened: dict[str, int] = {}
    for chapter in chapters:
        for thread_id in chapter.get("open_threads") or []:
            if any(marker in thread_id for marker in ("；", ";", "、", "以及")):
                raise ValueError(f"伏笔 ID 必须只表达一个原子问题: {thread_id}")
            if thread_id in opened:
                raise ValueError(f"结构化大纲伏笔 ID 重复: {thread_id}")
            opened[thread_id] = int(chapter["position"])
    return opened
