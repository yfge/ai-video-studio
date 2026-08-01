from app.utils.json_utils import extract_json_block

from . import story_novel_block_contract as block_contract
from . import story_novel_v3_prompts as prompts
from . import story_novel_v3_repair_length as repair_length
from .story_novel_chapter_brief_contract import validate_model_brief
from .story_novel_export_ai import TruncatedNovelOutput
from .story_novel_finish_reason import is_recoverable_length_finish_reason
from .story_novel_sentence_spans import audit_sentence_index
from .story_novel_v3_audit import audit_contracts, parse_proof_audit
from .story_novel_v3_repair_input import build_repair_input
from .story_novel_v3_truncation import recover_truncated_prose
from .story_novel_v4_call_snapshot import frozen_prompt_and_replay


async def generate_chapter_brief(revision, position, brief_input, generate_text):
    prompt = prompts.chapter_brief_prompt(brief_input)

    def parse(text):
        payload = extract_json_block(text)
        if not payload:
            raise ValueError("chapter brief 缺少 JSON")
        return validate_model_brief(payload, brief_input)

    return await _generate_with_format_repair(
        revision,
        prompt,
        parse,
        generate_text,
        stage=f"chapter_planning.{position}",
        max_tokens=12_000,
    )


async def generate_prose_blocks(
    revision, position, prose_input, expected_count, generate_text
):
    prompt = prompts.prose_blocks_prompt(prose_input)

    def parse(text):
        blocks = block_contract.parse_prose_block_response(text, expected_count)
        assembled = block_contract.assemble_prose_blocks(blocks)
        return {"block_contents": blocks, **assembled}

    try:
        return await _generate_with_format_repair(
            revision,
            prompt,
            parse,
            generate_text,
            stage=f"prose.{position}",
            max_tokens=block_contract.prose_token_budget(prose_input),
        )
    except TruncatedNovelOutput as exc:
        if not is_recoverable_length_finish_reason(exc.finish_reason):
            raise
        return await recover_truncated_prose(
            revision,
            position,
            prose_input,
            expected_count,
            prompt,
            exc,
            generate_text,
            block_contract.prose_token_budget(prose_input),
        )


async def audit_chapter(
    revision,
    position,
    *,
    content_text,
    sentence_index,
    expected_delta,
    canon,
    chapter_plan,
    future_claim_cards,
    visible_world_rules,
    generate_text,
    stage,
    max_calls,
    reserve_call=None,
    repair_focus=None,
    brief=None,
    established_background=None,
    current_state_contract=None,
    future_state_boundaries=None,
    before_call=None,
):
    contracts = audit_contracts(expected_delta, canon, chapter_plan)
    audit_input = {
        "position": position,
        "proof_contracts": contracts,
        "current_contract_context": prompts.audit_contract_context(
            chapter_plan, brief, expected_delta, canon, established_background
        ),
        "sentence_index": audit_sentence_index(sentence_index),
        "future_claim_cards": future_claim_cards,
        "future_state_boundaries": list(future_state_boundaries or []),
        "current_state_contract": dict(current_state_contract or {}),
        "visible_world_rules": visible_world_rules,
    }
    if repair_focus:
        audit_input["repair_focus"] = list(repair_focus)
    prompt = prompts.chapter_audit_prompt(audit_input)

    def parse(text):
        return parse_proof_audit(text, contracts, content_text)

    return await _generate_with_format_repair(
        revision,
        prompt,
        parse,
        generate_text,
        stage=stage,
        max_tokens=6000,
        temperature=0.1,
        max_calls=max_calls,
        reserve_call=reserve_call,
        before_call=before_call,
    )


async def repair_blocks(
    revision,
    position,
    *,
    blocks,
    failed_block_ids,
    violations,
    prose_input,
    generate_text,
    expected_delta=None,
    before_call=None,
):
    failed = set(failed_block_ids)
    length_contract = repair_length.repair_contract(
        blocks, failed, prose_input, violations
    )
    repair_input = build_repair_input(
        blocks,
        failed,
        violations,
        prose_input,
        length_contract,
        expected_delta,
    )
    prompt = prompts.local_block_repair_prompt(repair_input)
    parse = repair_length.repair_response_parser(blocks, failed, length_contract)

    return await _generate_with_format_repair(
        revision,
        prompt,
        parse,
        generate_text,
        stage=f"local_repair.{position}",
        max_tokens=4000,
        temperature=0.2,
        repair_prompt=lambda _prompt, raw, error: prompts.local_block_contract_retry_prompt(
            repair_input, raw, error
        ),
        before_call=before_call,
    )


async def _generate_with_format_repair(
    revision,
    prompt,
    parser,
    generate_text,
    *,
    stage,
    max_tokens,
    temperature=None,
    max_calls=None,
    reserve_call=None,
    repair_prompt=None,
    format_repair_max_tokens=4000,
    before_call=None,
):
    if max_calls is not None and max_calls < 1:
        raise ValueError("当前正文审计调用预算已耗尽")
    calls = []
    call_stage = reserve_call(stage) if reserve_call else stage
    prompt, text = frozen_prompt_and_replay(before_call, call_stage, prompt)
    if text is None:
        text = await generate_text(
            revision,
            prompt,
            stage=call_stage,
            max_tokens=max_tokens,
            **({"temperature": temperature} if temperature is not None else {}),
        )
    calls.append(dict(getattr(text, "invocation_evidence", {}) or {}))
    try:
        value = parser(str(text))
    except (TypeError, ValueError) as exc:
        if max_calls is not None and len(calls) >= max_calls:
            raise
        repair = (repair_prompt or prompts.format_repair_prompt)(
            prompt, str(text), str(exc)
        )
        repair_stage = f"{stage}.format_repair"
        call_stage = reserve_call(repair_stage) if reserve_call else repair_stage
        repair, text = frozen_prompt_and_replay(before_call, call_stage, repair)
        if text is None:
            text = await generate_text(
                revision,
                repair,
                stage=call_stage,
                max_tokens=format_repair_max_tokens,
                temperature=0.1,
            )
        calls.append(dict(getattr(text, "invocation_evidence", {}) or {}))
        value = parser(str(text))
    return value, _stage_metrics(calls)


def _stage_metrics(calls: list[dict]) -> dict:
    return {
        "calls": len(calls),
        "input_tokens": sum(int(item.get("input_tokens") or 0) for item in calls),
        "output_tokens": sum(int(item.get("output_tokens") or 0) for item in calls),
        "latency_ms": sum(int(item.get("latency_ms") or 0) for item in calls),
        "invocation_ids": [
            item["invocation_id"] for item in calls if item.get("invocation_id")
        ],
        "attempts": calls,
    }


def merge_stage_metrics(*metrics: dict | None) -> dict:
    candidates = sum([(metric or {}).get("attempts") or [] for metric in metrics], [])
    attempts = []
    seen = set()
    for item in candidates:
        key = item.get("invocation_id")
        if not key and item.get("call_scene") and item.get("response_hash"):
            key = (
                item.get("call_scene"),
                item.get("response_hash"),
                item.get("raw_response_hash"),
            )
        if not key:
            attempts.append(item)
        elif key not in seen:
            seen.add(key)
            attempts.append(item)
    return _stage_metrics(attempts)
