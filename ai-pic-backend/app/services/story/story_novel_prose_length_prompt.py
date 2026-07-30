"""Versioned model-facing projection of the frozen prose length contract."""

from __future__ import annotations

import copy


def controlled_prompt_input(prose_input: dict, control: dict) -> dict:
    """Expose one model-facing length contract without mutating frozen inputs."""
    if int(control.get("prompt_contract_version") or 1) == 1:
        return _legacy_prompt_input(prose_input, control)
    result = copy.deepcopy(prose_input)
    requested_length = copy.deepcopy(control["requested_length"])
    requested_blocks = copy.deepcopy(control["requested_blocks"])
    targets = {item["block_id"]: item["target_chars"] for item in requested_blocks}
    result["chapter_length"] = requested_length
    for beat in result["chapter_brief"].get("beats") or []:
        beat["target_chars"] = targets[beat["beat_id"]]
    result["generation_length_hints"] = {
        key: copy.deepcopy(control[key])
        for key in (
            "schema",
            "prompt_contract_version",
            "sample_source",
            "sample_count",
            "observed_response_ratio",
            "request_scale",
            "requested_length",
            "requested_blocks",
        )
    }
    result["generation_length_hints"].update(
        brief_hash=result["chapter_brief"].get("brief_hash"),
        instruction=(
            "chapter_length 与各 beat.target_chars 已由服务端按同 provider/model 的"
            "历史输出偏差统一校准；它们是本次输出唯一长度合同。不得恢复或猜测校准前"
            "数值，不得改变事件、beat、实体、状态或其他合同。"
        ),
    )
    return result


def _legacy_prompt_input(prose_input: dict, control: dict) -> dict:
    """Rebuild v1 prompts so already persisted invocation evidence stays valid."""
    result = copy.deepcopy(prose_input)
    result["generation_length_hints"] = {
        key: copy.deepcopy(control[key])
        for key in (
            "schema",
            "sample_source",
            "sample_count",
            "observed_response_ratio",
            "request_scale",
            "requested_length",
            "requested_blocks",
        )
    }
    result["generation_length_hints"].update(
        brief_hash=result["chapter_brief"].get("brief_hash"),
        instruction=(
            "这是服务端根据同 provider/model 已验收章节计算的内部长度校准，优先用于"
            "你对输出篇幅的估算。保持冻结 chapter_brief 与 chapter_length 不变；外层"
            "模板提及 beat.target_chars 或 chapter_length.target_chars 时，不要再次按"
            "那些数值估算输出量，而应按 requested_length/requested_blocks 估算。最终"
            "服务端仍以原 chapter_length 验收。不得改变事件、beat、实体、状态或合同。"
        ),
    )
    return result
