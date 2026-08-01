"""Deterministic length budgets for v3 local block repair."""

import re
from itertools import product

from app.utils.json_utils import extract_json_block

from .story_novel_block_contract import assemble_prose_blocks, replace_prose_blocks
from .story_novel_prose_integrity import prose_integrity_violations


def repair_contract(blocks, failed_ids, prose_input, violations):
    return replacement_length_contract(
        blocks,
        failed_ids,
        prose_input["chapter_length"],
        prose_input["chapter_brief"],
        violations,
    )


def replacement_length_contract(
    blocks, failed_ids: set[str], chapter_length, brief=None, violations=None
) -> dict:
    fixed = [item for item in blocks if item["block_id"] not in failed_ids]
    fixed_chars = sum(len(re.sub(r"\s+", "", item["content_text"])) for item in fixed)
    minimum = int(chapter_length["min_chars"])
    target = int(chapter_length["target_chars"])
    maximum = int(chapter_length["max_chars"])
    current_chars = sum(_chars(item["content_text"]) for item in blocks)
    repair_target = target
    if current_chars < minimum:
        headroom = max(0, target - minimum)
        repair_target = min(target, minimum + min(128, max(32, headroom // 5)))
    safety_margin = (
        min(max(32, target // 20), max(0, maximum - target))
        if current_chars > maximum
        else 0
    )
    repair_ceiling = maximum - safety_margin
    replacement_max = repair_ceiling - fixed_chars
    if replacement_max < 1:
        raise ValueError("只读 blocks 已超过章节最大长度，无法局部返修")
    replacement_min = max(1, minimum - fixed_chars)
    replacement_target = min(
        replacement_max, max(replacement_min, repair_target - fixed_chars)
    )
    contract = {
        "count_mode": "non_whitespace_chars",
        "fixed_chars": fixed_chars,
        "replacement_min_chars": replacement_min,
        "replacement_target_chars": replacement_target,
        "replacement_max_chars": replacement_max,
        "chapter_min_chars": minimum,
        "chapter_target_chars": target,
        "chapter_max_chars": maximum,
        "repair_model_target_chars": replacement_target,
        "repair_safety_margin_chars": safety_margin,
        "repair_chapter_ceiling_chars": repair_ceiling,
    }
    if brief and failed_ids:
        contract["replacement_blocks"] = _block_budgets(
            blocks, failed_ids, brief, replacement_target
        )
    codes = {item.get("reason_code") or item.get("code") for item in violations or []}
    if codes == {"length_out_of_range"}:
        contract["selection_policy"] = "complete_failed_blocks_first_v2"
    return contract


def _block_budgets(blocks, failed_ids, brief, total_target):
    beat_targets = {
        item.get("beat_id"): int(item.get("target_chars") or 0)
        for item in brief.get("beats") or []
    }
    selected = [item for item in blocks if item["block_id"] in failed_ids]
    weights = [
        beat_targets.get(item["block_id"]) or _chars(item["content_text"])
        for item in selected
    ]
    total_weight = sum(weights) or len(weights) or 1
    assigned, remaining = [], total_target
    for index, (item, weight) in enumerate(zip(selected, weights, strict=True)):
        target = (
            remaining
            if index == len(selected) - 1
            else max(1, total_target * weight // total_weight)
        )
        remaining -= target
        assigned.append(
            {
                "block_id": item["block_id"],
                "original_chars": _chars(item["content_text"]),
                "min_chars": max(1, target * 80 // 100),
                "target_chars": target,
                "max_chars": max(1, target * 120 // 100),
            }
        )
    return assigned


def assemble_valid_repair(blocks, replacements, contract: dict) -> dict:
    _validate_replacement_blocks(replacements, contract)
    updated = replace_prose_blocks(blocks, replacements)
    integrity = prose_integrity_violations(updated)
    if integrity:
        raise ValueError(integrity[0]["message"])
    assembled = assemble_prose_blocks(updated)
    actual = int(assembled["char_count"])
    minimum = int(contract["chapter_min_chars"])
    maximum = int(contract["chapter_max_chars"])
    if not minimum <= actual <= maximum:
        raise ValueError(
            f"local repair 合并正文长度为 {actual}，必须为 {minimum}–{maximum}；"
            "请严格遵守 replacement_length"
        )
    return {"block_contents": updated, **assembled}


def assemble_hybrid_repair(blocks, first, second, contract: dict) -> dict:
    """Select complete model-authored blocks from two bounded repair attempts."""
    first_map = {item.get("block_id"): item for item in first}
    second_map = {item.get("block_id"): item for item in second}
    if set(first_map) != set(second_map):
        raise ValueError("local repair 两次响应的 block ID 不一致")
    target = int(contract["chapter_target_chars"])
    candidates = []
    block_ids = sorted(first_map)
    for choices in product((0, 1), repeat=len(block_ids)):
        replacements = [
            (first_map if choice == 0 else second_map)[block_id]
            for block_id, choice in zip(block_ids, choices, strict=True)
        ]
        try:
            value = assemble_valid_repair(blocks, replacements, contract)
        except ValueError:
            continue
        candidates.append((abs(int(value["char_count"]) - target), choices, value))
    if not candidates:
        raise ValueError("local repair 两次完整块无法组合到章节长度区间")
    return min(candidates, key=lambda item: (item[0], item[1]))[2]


def assemble_minimal_change_repair(blocks, attempts, contract: dict) -> dict:
    """Prefer all failed-block replacements, then minimize fallback changes."""
    maps = [{item.get("block_id"): item for item in rows} for rows in attempts]
    block_ids = sorted(maps[0])
    if any(set(value) != set(block_ids) for value in maps):
        raise ValueError("local repair 多次响应的 block ID 不一致")
    target, candidates = int(contract["chapter_target_chars"]), []
    fallback_error = None
    try:
        return assemble_valid_repair(
            blocks, [maps[-1][block_id] for block_id in block_ids], contract
        )
    except ValueError as exc:
        fallback_error = exc
    for choices in product(range(len(maps) + 1), repeat=len(block_ids)):
        replacements = [
            maps[choice - 1][block_id]
            for block_id, choice in zip(block_ids, choices, strict=True)
            if choice
        ]
        if not replacements:
            continue
        try:
            value = assemble_valid_repair(blocks, replacements, contract)
        except ValueError:
            continue
        candidates.append(
            (len(replacements), abs(int(value["char_count"]) - target), choices, value)
        )
    if not candidates:
        if fallback_error:
            raise fallback_error
        raise ValueError("local repair 没有满足长度区间的最小改动组合")
    return min(candidates, key=lambda item: item[:3])[3]


def repair_response_parser(blocks, failed_ids: set[str], contract: dict):
    """Build a two-attempt parser that may combine complete replacement blocks."""
    prior = None

    def parse(text):
        nonlocal prior
        payload = extract_json_block(text) or {}
        replacements = list(payload.get("replacements") or [])
        if (
            set(payload) != {"replacements"}
            or {item.get("block_id") for item in replacements} != failed_ids
        ):
            raise ValueError("local repair 未精确覆盖失败 blocks")
        try:
            if contract.get("selection_policy") == "complete_failed_blocks_first_v2":
                return assemble_minimal_change_repair(
                    blocks, [*([prior] if prior else []), replacements], contract
                )
            return assemble_valid_repair(blocks, replacements, contract)
        except ValueError:
            if prior is not None:
                return assemble_hybrid_repair(blocks, prior, replacements, contract)
            prior = replacements
            raise

    return parse


def _validate_replacement_blocks(replacements, contract):
    empty = [
        item.get("block_id")
        for item in replacements
        if not _chars(item.get("content_text") or "")
    ]
    if empty:
        raise ValueError(f"local repair block 正文为空: {', '.join(empty)}")


def _chars(value):
    return len(re.sub(r"\s+", "", value))
