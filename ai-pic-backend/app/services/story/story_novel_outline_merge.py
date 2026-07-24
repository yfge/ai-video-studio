"""Merge frozen outline prose with machine-generated chapter contracts."""

from __future__ import annotations

from .story_novel_canon_service import validate_generation_plan
from .story_novel_thread_schedule import payoffs_by_position
from .story_novel_timeline_contract import compile_timeline_bindings

_OUTLINE_KEYS = (
    "position",
    "title",
    "goal",
    "key_events",
    "character_focus",
    "open_threads",
    "end_state",
    "min_chars",
    "target_chars",
    "max_chars",
    "length_source",
    "length",
)
_QUOTE_VARIANTS = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"'})


def merge_frozen_chapters(
    chapters: list[dict],
    frozen_spec: dict | None,
    canon: dict,
    thread_payoffs: list[dict] | None = None,
    *,
    validate: bool = True,
) -> list[dict]:
    if not frozen_spec:
        return compile_timeline_bindings(canon, chapters)
    generated = {int(item["position"]): item for item in chapters}
    sources = list(frozen_spec.get("chapters") or [])
    if set(generated) != {int(item["position"]) for item in sources}:
        raise ValueError("冻结大纲与章节规划的章节位置不一致")
    thread_map = _thread_id_map(chapters, sources) if thread_payoffs is None else None
    scheduled = (
        payoffs_by_position(thread_payoffs) if thread_payoffs is not None else {}
    )
    merged = []
    for source in sources:
        machine = generated[int(source["position"])]
        _require_authoritative_event_order(machine, source)
        row = {
            **machine,
            **{key: source[key] for key in _OUTLINE_KEYS if key in source},
        }
        row["payoffs_due"] = (
            list(scheduled.get(int(source["position"]), []))
            if thread_map is None
            else _rewrite_payoffs(machine.get("payoffs_due") or [], thread_map)
        )
        merged.append(row)
    compiled = compile_timeline_bindings(canon, merged)
    if validate:
        validate_generation_plan(canon, compiled)
    return compiled


def _require_authoritative_event_order(machine: dict, source: dict) -> None:
    if "key_events" not in source:
        return
    generated = list(machine.get("key_events") or [])
    frozen = list(source.get("key_events") or [])
    if [_event_key(item) for item in generated] != [
        _event_key(item) for item in frozen
    ]:
        raise ValueError(
            f"第 {int(source['position'])} 章 key_events 必须逐字、同序复制冻结大纲"
        )


def _event_key(value: str) -> str:
    return value.translate(_QUOTE_VARIANTS)


def _thread_id_map(chapters: list[dict], sources: list[dict]) -> dict[str, list[str]]:
    payoff_positions = _payoff_positions(chapters)
    mapping: dict[str, list[str]] = {}
    seen_machine: set[str] = set()
    seen_source: set[str] = set()
    generated = {int(item["position"]): item for item in chapters}
    for source in sources:
        position = int(source["position"])
        machine_ids = list(generated[position].get("open_threads") or [])
        source_ids = list(source.get("open_threads") or [])
        _require_unique(machine_ids, seen_machine, position, "规划")
        _require_unique(source_ids, seen_source, position, "结构化大纲")
        pairs = _thread_pairs(position, machine_ids, source_ids, payoff_positions)
        for machine_id, targets in pairs:
            mapping[machine_id] = targets
    return mapping


def _thread_pairs(
    position: int,
    machine_ids: list[str],
    source_ids: list[str],
    payoff_positions: dict[str, tuple[int, ...]],
) -> list[tuple[str, list[str]]]:
    if len(machine_ids) == len(source_ids):
        return [
            (machine_id, [source_id])
            for machine_id, source_id in zip(machine_ids, source_ids, strict=True)
        ]
    if len(source_ids) == 1 and len(machine_ids) > 1:
        schedules = {payoff_positions.get(machine_id, ()) for machine_id in machine_ids}
        if len(schedules) == 1:
            return [(machine_id, source_ids) for machine_id in machine_ids]
    if len(machine_ids) == 1 and len(source_ids) > 1:
        return [(machine_ids[0], source_ids)]
    raise ValueError(
        f"第 {position} 章结构化伏笔数量与规划不一致，无法确定性映射: "
        f"{len(source_ids)} != {len(machine_ids)}"
    )


def _payoff_positions(chapters: list[dict]) -> dict[str, tuple[int, ...]]:
    positions: dict[str, list[int]] = {}
    for chapter in chapters:
        for thread_id in chapter.get("payoffs_due") or []:
            positions.setdefault(thread_id, []).append(int(chapter["position"]))
    return {thread_id: tuple(value) for thread_id, value in positions.items()}


def _require_unique(
    values: list[str], seen: set[str], position: int, label: str
) -> None:
    duplicates = seen.intersection(values)
    if duplicates or len(values) != len(set(values)):
        raise ValueError(
            f"第 {position} 章{label}伏笔 ID 重复: {sorted(duplicates or set(values))}"
        )
    seen.update(values)


def _rewrite_payoffs(payoffs: list[str], thread_map: dict[str, list[str]]) -> list[str]:
    rewritten: list[str] = []
    for thread_id in payoffs:
        if thread_id not in thread_map:
            raise ValueError(f"规划回收的伏笔缺少冻结大纲映射: {thread_id}")
        for source_id in thread_map[thread_id]:
            if source_id not in rewritten:
                rewritten.append(source_id)
    return rewritten
