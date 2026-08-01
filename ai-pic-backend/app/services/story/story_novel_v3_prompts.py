"""Prompts for the v3 plan, prose-block, proof-audit, and local-repair stages."""

from __future__ import annotations

import copy
import re

from app.utils.json_utils import extract_json_block

from .story_novel_audit_contract_context import audit_contract_context  # noqa: F401
from .story_novel_domain import json_prompt_payload
from .story_novel_prompt_renderer import render_novel_prompt
from .story_novel_v3_repair_guidance import safe_repair_issues


def chapter_brief_prompt(brief_input: dict) -> str:
    return render_novel_prompt(
        "story_novel_chapter_brief_v3",
        brief_input_json=json_prompt_payload(brief_input),
    )


def chapter_package_prompt(package_input: dict) -> str:
    return render_novel_prompt(
        "story_novel_chapter_package_v3",
        package_input_json=json_prompt_payload(package_input),
    )


def prose_blocks_prompt(prose_input: dict) -> str:
    return render_novel_prompt(
        "story_novel_prose_blocks_v3",
        prose_input_json=json_prompt_payload(prose_input),
    )


def prose_blocks_continuation_prompt(
    prose_input: dict, complete_blocks: list[dict], missing_block_ids: list[str]
) -> str:
    return render_novel_prompt(
        "story_novel_prose_continuation_v3",
        prose_input_json=json_prompt_payload(prose_input),
        complete_blocks_json=json_prompt_payload(complete_blocks),
        missing_block_ids_repr=repr(missing_block_ids),
        first_missing_block_id=missing_block_ids[0] if missing_block_ids else "B01",
    )


def chapter_audit_prompt(audit_input: dict) -> str:
    return render_novel_prompt(
        "story_novel_proof_audit_v3",
        audit_input_json=json_prompt_payload(audit_input),
    )


def local_block_repair_prompt(repair_input: dict) -> str:
    return render_novel_prompt(
        "story_novel_local_block_repair_v3",
        repair_input_json=json_prompt_payload(repair_input),
    )


def local_block_contract_retry_prompt(
    repair_input: dict, previous_response: str, error: str
) -> str:
    parsed = extract_json_block(previous_response)
    length_contract = repair_input.get("replacement_length") or {}
    diagnostics = _replacement_length_diagnostics(parsed, length_contract)
    length_action = _replacement_retry_action(diagnostics, length_contract)
    length_retry = (
        repair_input.get("rewrite_mode")
        in {"length_contract_from_chapter_brief", "compress_current_blocks"}
        or "replacement_length" in error
        or "合并正文长度" in error
    )
    feedback = {"validation_error": error}
    if length_retry:
        retry_contract = _calibrated_retry_contract(length_contract, diagnostics)
        feedback.update(
            required_action=(
                "上一响应未满足正文合同。逐项查看 block_length_diagnostics："
                "actual_chars 高于 max_chars "
                "必须重写至 target_chars，低于 min_chars 才续写至 target_chars；"
                "全部 replacements 的非空白字符总数必须落入 replacement_length。"
            ),
            block_length_diagnostics=diagnostics,
        )
        source_key = f"previous_replacements_to_{length_action}"
        feedback[source_key] = parsed or previous_response
        feedback[f"{length_action}_instruction"] = _retry_instruction(length_action)
        current_context = repair_input.get("current_chapter_context") or {}
        current_requirements = repair_input.get("current_contract_requirements") or {}
        retry_input = {
            "rewrite_mode": f"{length_action}_previous_replacements",
            "failed_block_ids": repair_input.get("failed_block_ids") or [],
            "retry_feedback": feedback,
            "replacement_length": retry_contract,
            "current_chapter_context": current_context,
            "current_contract_requirements": current_requirements,
            "current_issue_constraints": safe_repair_issues(
                repair_input.get("violations")
            ),
            "neighbor_blocks": repair_input.get("neighbor_blocks") or [],
            "visible_canon": repair_input.get("visible_canon") or {},
            "writing_style": repair_input.get("writing_style") or {},
        }
    else:
        feedback.update(
            required_action=(
                "只编辑 previous_response_to_revise 中导致 validation_error 的完整块，"
                "其他 replacement 保持不变。若错误指出 replacement 与只读 neighbor "
                "重复，必须删除全部重叠句段，并仅用当前章动作、冲突、对话、感官或"
                "即时判断补足该块 target_chars；不得复制 neighbor 或恢复旧错误设定。"
            ),
            previous_response_to_revise=parsed or previous_response,
            block_length_diagnostics=diagnostics,
        )
        current_context = repair_input.get("current_chapter_context") or {}
        current_requirements = repair_input.get("current_contract_requirements") or {}
        retry_input = {
            "rewrite_mode": "repair_previous_replacements",
            "failed_block_ids": repair_input.get("failed_block_ids") or [],
            "retry_feedback": feedback,
            "replacement_length": length_contract,
            "current_chapter_context": current_context,
            "current_contract_requirements": current_requirements,
            "current_issue_constraints": safe_repair_issues(
                repair_input.get("violations")
            ),
            "neighbor_blocks": repair_input.get("neighbor_blocks") or [],
            "visible_canon": repair_input.get("visible_canon") or {},
            "writing_style": repair_input.get("writing_style") or {},
        }
    return local_block_repair_prompt(retry_input)


def _replacement_retry_action(diagnostics: list[dict], contract: dict) -> str:
    actual = int(contract.get("fixed_chars") or 0) + sum(
        int(item.get("actual_chars") or 0) for item in diagnostics
    )
    if actual < int(contract.get("chapter_min_chars") or 0):
        return "expand"
    return "compress"


def _calibrated_retry_contract(contract: dict, diagnostics: list[dict]) -> dict:
    """Counter observed model bias while preserving the parser's hard contract."""
    result = copy.deepcopy(contract)
    requested = int(contract.get("repair_model_target_chars") or 0)
    actual = sum(int(item.get("actual_chars") or 0) for item in diagnostics)
    if not requested or not actual:
        return result
    minimum = max(1, int(contract.get("replacement_min_chars") or 1))
    maximum = max(minimum, int(contract.get("replacement_max_chars") or minimum))
    retry_target = min(maximum, max(minimum, round(requested * requested / actual)))
    result.update(
        replacement_target_chars=retry_target,
        repair_model_target_chars=retry_target,
        retry_source_actual_chars=actual,
        retry_model_target_chars=retry_target,
    )
    result["replacement_blocks"] = _retry_block_budgets(
        contract.get("replacement_blocks") or [], retry_target
    )
    return result


def _retry_block_budgets(blocks: list[dict], total: int) -> list[dict]:
    weights = [max(1, int(item.get("target_chars") or 0)) for item in blocks]
    weight_sum, remaining, result = sum(weights) or 1, total, []
    for index, (item, weight) in enumerate(zip(blocks, weights, strict=True)):
        target = remaining if index == len(blocks) - 1 else total * weight // weight_sum
        remaining -= target
        result.append(
            {
                **item,
                "min_chars": max(1, target * 80 // 100),
                "target_chars": target,
                "max_chars": max(1, target * 120 // 100),
            }
        )
    return result


def _retry_instruction(action: str) -> str:
    if action == "expand":
        return (
            "只编辑 previous_replacements_to_expand：把不足的块续写至各自 target_chars，"
            "只补当前场景动作、冲突、对话、感官与即时判断；不得新增人物关系、知识、"
            "权限、物件所有权、跨章线索或未来事件。"
        )
    return (
        "只编辑 previous_replacements_to_compress：删除或合并重复讲解、重复动作与景物，"
        "不得改写成摘要；必须保留 current_contract_requirements 并修正 "
        "current_issue_constraints，不得增加知识或新增情节。"
    )


def _replacement_length_diagnostics(payload, contract: dict) -> list[dict]:
    replacements = {
        str(item.get("block_id")): item.get("content_text") or ""
        for item in (payload or {}).get("replacements") or []
        if item.get("block_id")
    }
    return [
        {
            **budget,
            "actual_chars": len(re.sub(r"\s+", "", replacements.get(block_id, ""))),
        }
        for budget in contract.get("replacement_blocks") or []
        if (block_id := str(budget.get("block_id") or ""))
    ]


def format_repair_prompt(original_prompt: str, raw: str, error: str) -> str:
    return render_novel_prompt(
        "story_novel_format_repair_v3",
        original_prompt=original_prompt,
        raw_response=raw,
        error=error,
    )
