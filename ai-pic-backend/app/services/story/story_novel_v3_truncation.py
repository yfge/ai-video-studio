"""Recover complete prose blocks from one provider truncation."""

from __future__ import annotations

from app.utils.json_utils import extract_json_block

from .story_novel_block_contract import (
    assemble_prose_blocks,
    parse_prose_blocks,
    recover_complete_prose_blocks,
)
from .story_novel_finish_reason import is_recoverable_length_finish_reason
from .story_novel_v3_prompts import prose_blocks_continuation_prompt


async def recover_truncated_prose(
    revision,
    position,
    prose_input,
    expected_count,
    original_prompt,
    error,
    generate_text,
    max_tokens,
    *,
    before_call=None,
):
    if not is_recoverable_length_finish_reason(error.finish_reason):
        raise error
    complete = recover_complete_prose_blocks(error.partial_text)
    attempts = [dict(error.invocation_evidence or {})]
    if not complete:
        retry_prompt = original_prompt
        if before_call:
            before_call(f"prose.{position}.truncation_retry", retry_prompt)
        retry = await generate_text(
            revision,
            retry_prompt,
            stage=f"prose.{position}.truncation_retry",
            max_tokens=max_tokens,
        )
        attempts.append(_evidence(retry))
        blocks = parse_prose_blocks(
            extract_json_block(str(retry)), expected_count=expected_count
        )
        return _result(blocks, attempts)
    expected_ids = [f"B{index:02d}" for index in range(1, expected_count + 1)]
    missing = expected_ids[len(complete) :]
    if not missing:
        return _result(complete, attempts)
    continuation_prompt = prose_blocks_continuation_prompt(
        prose_input, complete, missing
    )
    if before_call:
        before_call(f"prose.{position}.truncation_continue", continuation_prompt)
    continuation = await generate_text(
        revision,
        continuation_prompt,
        stage=f"prose.{position}.truncation_continue",
        max_tokens=max_tokens,
        temperature=0.2,
    )
    attempts.append(_evidence(continuation))
    payload = extract_json_block(str(continuation)) or {}
    additions = list(payload.get("blocks") or [])
    if [item.get("block_id") for item in additions] != missing:
        raise ValueError("截断续写未精确覆盖缺失 blocks")
    blocks = parse_prose_blocks(
        {"blocks": [*complete, *additions]}, expected_count=expected_count
    )
    return _result(blocks, attempts)


def _result(blocks, attempts):
    prose = {"block_contents": blocks, **assemble_prose_blocks(blocks)}
    return prose, {
        "calls": len(attempts),
        "input_tokens": sum(int(item.get("input_tokens") or 0) for item in attempts),
        "output_tokens": sum(int(item.get("output_tokens") or 0) for item in attempts),
        "latency_ms": sum(int(item.get("latency_ms") or 0) for item in attempts),
        "invocation_ids": [
            item["invocation_id"] for item in attempts if item.get("invocation_id")
        ],
        "attempts": attempts,
    }


def _evidence(text):
    return dict(getattr(text, "invocation_evidence", {}) or {})
