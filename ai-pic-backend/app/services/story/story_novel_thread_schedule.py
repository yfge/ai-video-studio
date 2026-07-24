"""Provider-planned, deterministically validated frozen-outline thread payoffs."""

from __future__ import annotations

from typing import Awaitable, Callable

from app.utils.json_utils import extract_json_block

from .story_novel_canon_service import canonical_json
from .story_novel_plan_quality import MAX_PAYOFFS_PER_CHAPTER
from .story_novel_task_guard import generate_text_unless_cancelled
from .story_novel_thread_schedule_repair import (
    extracted_schedule_rows,
    merge_schedule_repairs,
    repair_conflict_ids,
    thread_schedule_repair_prompt,
)

GenerateText = Callable[..., Awaitable[str]]


async def compile_thread_payoffs(
    db,
    task,
    generate_text: GenerateText,
    revision,
    frozen_spec: dict | None,
) -> list[dict] | None:
    contract = thread_schedule_contract(frozen_spec)
    if contract is None:
        return None
    thread_count = sum(len(row["open_threads"]) for row in contract)
    if not thread_count:
        return []
    prompt = thread_schedule_prompt(contract)
    max_tokens = max(16000, thread_count * 300)
    text = await generate_text_unless_cancelled(
        db, task, generate_text, revision, prompt, max_tokens=max_tokens
    )
    original_rows = extracted_schedule_rows(text)
    schedule, error = parse_thread_payoffs(text, contract)
    if schedule is None:
        conflicts = repair_conflict_ids(original_rows, contract)
        repair = thread_schedule_repair_prompt(
            error, conflicts, contract, original_rows
        )
        text = await generate_text_unless_cancelled(
            db, task, generate_text, revision, repair, max_tokens=max_tokens
        )
        try:
            repaired_rows = merge_schedule_repairs(
                original_rows, text, contract, conflicts
            )
            schedule = _validate_schedule(repaired_rows, contract)
            error = None
        except (KeyError, TypeError, ValueError) as exc:
            schedule, error = None, str(exc)
    if schedule is None:
        raise ValueError(f"伏笔回收调度无效: {error}")
    return schedule


def thread_schedule_contract(frozen_spec: dict | None) -> list[dict] | None:
    if not frozen_spec:
        return None
    chapters = list(frozen_spec.get("chapters") or [])
    contract = [
        {
            "position": int(row["position"]),
            "title": str(row.get("title") or ""),
            "goal": str(row.get("goal") or ""),
            "open_threads": list(row.get("open_threads") or []),
            "key_events": list(row.get("key_events") or []),
            "end_state": str(row.get("end_state") or ""),
        }
        for row in chapters
    ]
    positions = [row["position"] for row in contract]
    if positions != list(range(1, len(contract) + 1)):
        raise ValueError("冻结大纲章节位置不连续")
    _source_threads(contract)
    return contract


def thread_schedule_prompt(contract: list[dict]) -> str:
    return (
        "只依据冻结 structured_outline 的标题、目标、关键事件、线索和章末状态"
        "调度全书伏笔回收，不写章节合同或正文。"
        "\n每个 open_threads 值都是稳定 thread_id，必须且只能回收一次；"
        "payoff_position 必须严格晚于打开章。"
        "\n每条回收必须逐字复制目标章的一条 key_events 作为 evidence_key_event；"
        "同一事件确实同时回答多条语义相关线索时，允许共享同一个 exact "
        "evidence_key_event；无论是否共享，每章最多回收 "
        f"{MAX_PAYOFFS_PER_CHAPTER} 条。"
        "\n只输出严格 JSON："
        '{"thread_payoffs":[{"thread_id":"原样 ID","payoff_position":2,'
        '"evidence_key_event":"目标章 key_events 原文"}]}'
        f"\n冻结输入：{canonical_json({'chapters': contract})}"
    )


def parse_thread_payoffs(
    text: str, contract: list[dict]
) -> tuple[list[dict] | None, str | None]:
    try:
        payload = extract_json_block(text)
        if not isinstance(payload, dict) or set(payload) != {"thread_payoffs"}:
            raise ValueError("必须只返回 thread_payoffs JSON")
        rows = payload["thread_payoffs"]
        if not isinstance(rows, list):
            raise ValueError("thread_payoffs 必须是数组")
        return _validate_schedule(rows, contract), None
    except (KeyError, TypeError, ValueError) as exc:
        return None, str(exc)


def payoffs_by_position(schedule: list[dict]) -> dict[int, list[str]]:
    result: dict[int, list[str]] = {}
    for row in schedule:
        result.setdefault(int(row["payoff_position"]), []).append(row["thread_id"])
    return result


def _validate_schedule(rows: list, contract: list[dict]) -> list[dict]:
    opened = _source_threads(contract)
    events = {row["position"]: row["key_events"] for row in contract}
    seen: dict[str, dict] = {}
    positions: dict[int, list[dict]] = {}
    errors: list[str] = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict) or set(row) != {
            "thread_id",
            "payoff_position",
            "evidence_key_event",
        }:
            errors.append(
                f"第 {index} 条调度必须只有 "
                "thread_id/payoff_position/evidence_key_event"
            )
            continue
        thread_id, payoff = row["thread_id"], row["payoff_position"]
        if not isinstance(thread_id, str) or not thread_id:
            errors.append(f"第 {index} 条 thread_id 必须是非空字符串")
            continue
        normalized = {
            "thread_id": thread_id,
            "payoff_position": payoff,
            "evidence_key_event": row["evidence_key_event"],
        }
        if thread_id in seen:
            errors.append(f"伏笔重复回收: {thread_id}")
        else:
            seen[thread_id] = normalized
        known = thread_id in opened
        if not known:
            errors.append(f"调度包含未知伏笔: {thread_id}")
        valid_position = type(payoff) is int and payoff in events
        if not valid_position:
            errors.append(f"伏笔 {thread_id} 的 payoff_position 无效: {payoff!r}")
            continue
        positions.setdefault(payoff, []).append(normalized)
        if known and payoff <= opened[thread_id]:
            errors.append(
                f"伏笔提前回收: {thread_id} (open={opened[thread_id]}, payoff={payoff})"
            )
        evidence = row["evidence_key_event"]
        if not isinstance(evidence, str) or evidence not in events[payoff]:
            errors.append(
                f"第 {payoff} 章 evidence_key_event 未逐字复制: "
                f"{thread_id}={evidence!r}"
            )
    missing = [thread_id for thread_id in opened if thread_id not in seen]
    if missing:
        errors.append(f"伏笔调度遗漏: {missing}")
    for position, scheduled in positions.items():
        if len(scheduled) > MAX_PAYOFFS_PER_CHAPTER:
            errors.append(
                f"第 {position} 章集中回收 {len(scheduled)} 条伏笔，"
                f"超过单章上限 {MAX_PAYOFFS_PER_CHAPTER}"
            )
    if errors:
        unique = list(dict.fromkeys(errors))
        raise ValueError(
            f"伏笔回收调度确定性诊断失败（共 {len(unique)} 项）: " + "；".join(unique)
        )
    return [seen[thread_id] for thread_id in opened]


def _source_threads(contract: list[dict]) -> dict[str, int]:
    opened: dict[str, int] = {}
    for chapter in contract:
        for thread_id in chapter["open_threads"]:
            if not isinstance(thread_id, str) or not thread_id:
                raise ValueError("冻结大纲 thread_id 必须是非空字符串")
            if thread_id in opened:
                raise ValueError(f"冻结大纲 thread_id 重复: {thread_id}")
            opened[thread_id] = chapter["position"]
    return opened
