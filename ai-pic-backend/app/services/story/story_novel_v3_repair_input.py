"""Build bounded v3 block-repair inputs without encouraging source copying."""

import copy
import re

from .story_novel_block_contract import repair_block_context


def build_repair_input(
    blocks,
    failed: set[str],
    violations,
    prose_input,
    length_contract,
    expected_delta=None,
) -> dict:
    violation_codes = {
        item.get("reason_code") or item.get("code") for item in violations
    }
    pure_length = violation_codes == {"length_out_of_range"}
    length_action = _length_action(violations, blocks, prose_input)
    failed_blocks = [item for item in blocks if item["block_id"] in failed]
    neighbors = [
        item
        for item in repair_block_context(blocks, failed)
        if not item.get("editable")
    ]
    result = {
        "failed_block_ids": sorted(failed),
        "failed_blocks": failed_blocks,
        "neighbor_blocks": neighbors,
        "violations": violations,
        "chapter_brief": prose_input["chapter_brief"],
        "current_chapter_context": prose_input.get("current_chapter_context") or {},
        "current_contract_requirements": _current_contract_requirements(
            prose_input["chapter_brief"], failed, expected_delta or {}
        ),
        "visible_canon": prose_input["visible_canon"],
        "chapter_length": prose_input["chapter_length"],
        "writing_style": prose_input.get("writing_style") or {},
        "replacement_length": length_contract,
    }
    if not pure_length:
        return result
    if length_action == "compress":
        return {
            "rewrite_mode": "compress_current_blocks",
            "length_rewrite_instruction": (
                "纯超长失败：只压缩 failed_blocks 的现有安全正文。保持事件顺序、"
                "人物、关系、地点、知识和动作完成度不变，不得从 brief 重新创作。"
            ),
            **result,
            "chapter_brief": _failed_brief(result["chapter_brief"], failed),
            "neighbor_blocks": [
                _neighbor_excerpt(item, blocks, failed) for item in neighbors
            ],
        }
    return {
        "rewrite_mode": "length_contract_from_chapter_brief",
        "length_rewrite_instruction": (
            "纯长度失败：失败块正文被刻意隐藏，必须根据同 ID chapter_brief beat "
            "重新写作，不得复原、猜测或复制旧正文。"
        ),
        **result,
        "failed_blocks": [_source_free(item) for item in failed_blocks],
        "chapter_brief": _failed_brief(result["chapter_brief"], failed),
        "neighbor_blocks": [
            _neighbor_excerpt(item, blocks, failed) for item in neighbors
        ],
    }


def _length_action(violations, blocks: list[dict], prose_input: dict) -> str | None:
    explicit = {
        item.get("length_action")
        for item in violations
        if item.get("length_action") in {"compress", "expand"}
    }
    if len(explicit) == 1:
        return explicit.pop()
    actual = sum(
        len(re.sub(r"\s+", "", item.get("content_text") or "")) for item in blocks
    )
    maximum = int((prose_input.get("chapter_length") or {}).get("max_chars") or 0)
    return "compress" if maximum and actual > maximum else "expand"


def _current_contract_requirements(
    brief: dict, failed: set[str], expected_delta: dict
) -> dict:
    refs = []
    for beat in brief.get("beats") or []:
        if beat.get("beat_id") not in failed:
            continue
        refs.extend(f"event:{value}" for value in beat.get("bound_event_ids") or [])
        refs.extend(beat.get("effect_contract_ids") or [])
    wanted = list(dict.fromkeys(refs))
    contracts = {
        item.get("contract_id"): item
        for item in expected_delta.get("proof_contracts") or []
        if isinstance(item, dict) and item.get("contract_id")
    }
    return {
        "scope": "current_chapter_only",
        "proof_contracts": [
            copy.deepcopy(contracts[contract_id])
            for contract_id in wanted
            if contract_id in contracts
        ],
    }


def _source_free(item: dict) -> dict:
    return {
        key: value
        for key, value in {
            "block_id": item.get("block_id"),
            "editable": item.get("editable"),
            "original_chars": len(re.sub(r"\s+", "", item.get("content_text") or "")),
        }.items()
        if value is not None
    }


def _failed_brief(brief: dict, failed: set[str]) -> dict:
    return {
        key: value
        for key, value in {
            "beats": [
                item
                for item in brief.get("beats") or []
                if item.get("beat_id") in failed
            ],
            "emotional_continuity": brief.get("emotional_continuity"),
            "causal_bridge": brief.get("causal_bridge"),
        }.items()
        if value
    }


def _neighbor_excerpt(item: dict, blocks: list[dict], failed: set[str]) -> dict:
    positions = {row["block_id"]: index for index, row in enumerate(blocks)}
    failed_positions = [positions[value] for value in failed]
    before = positions[item["block_id"]] < min(failed_positions)
    text = item.get("content_text") or ""
    return {
        **item,
        "content_text": text[-160:] if before else text[:160],
        "excerpt": "tail" if before else "head",
    }
