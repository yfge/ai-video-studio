"""One bounded prose repair around length and extracted-state hard gates."""

from __future__ import annotations

from app.schemas.story_novel_longform import StoryNovelChapterGeneration
from app.utils.json_utils import extract_json_block

from . import story_novel_repair_safety as repair
from .story_novel_ai_prompts import chapter_gate_repair_prompt, chapter_prompt
from .story_novel_context_utils import prompt_chapter_contract
from .story_novel_evidence_rules import (
    evidence_violations,
    required_event_anchor_violations,
    timeline_evidence_violations,
)
from .story_novel_gate_support import future_event_catalog, premature_plan_violations
from .story_novel_length_contract import (
    chapter_length_range,
    chapter_output_tokens,
    non_whitespace_chars,
)
from .story_novel_plot_contract import validated_plot_delta
from .story_novel_prose_canon_gate import revision_prose_canon_violations
from .story_novel_state_extraction import StateExtractionError, extract_chapter_state
from .story_novel_state_validator import validate_state_delta


def parse_chapter(text: str) -> tuple[dict | None, str | None]:
    try:
        payload = extract_json_block(text)
        if not payload:
            raise ValueError("missing JSON object")
        if not payload.get("content_text") and payload.get("body"):
            payload = {**payload, "content_text": payload["body"]}
        return StoryNovelChapterGeneration.model_validate(payload).model_dump(), None
    except (ValueError, TypeError) as exc:
        return None, str(exc)


async def generate_validated_chapter(
    revision,
    *,
    chapter_plan: dict,
    context_pack: dict,
    generate_text,
) -> dict:
    text = await _generate_initial_body(
        revision, chapter_plan, context_pack, generate_text
    )
    first_evaluation = await _evaluate(
        revision,
        text,
        chapter_plan=chapter_plan,
        context_pack=context_pack,
        generate_text=generate_text,
    )
    if first_evaluation["passed"] or first_evaluation["state_extraction_evidence_only"]:
        return {**first_evaluation, "body_repair_count": 0}

    prior = first_evaluation["result"] or {
        "raw": text[:8000],
        "validation_error": first_evaluation.get("parse_error"),
    }
    repaired = await _generate_repaired_body(
        revision,
        chapter_plan,
        context_pack,
        first_evaluation,
        prior,
        generate_text,
    )
    final_evaluation = await _evaluate(
        revision,
        repaired,
        chapter_plan=chapter_plan,
        context_pack=context_pack,
        generate_text=generate_text,
    )
    extraction_repairs = sum(
        int(item.get("state_extraction_repair_count") or 0)
        for item in (first_evaluation, final_evaluation)
    )
    selected = repair.select_repair_evaluation(first_evaluation, final_evaluation)
    return {
        **selected,
        "body_repair_count": 1,
        "state_extraction_repair_count": extraction_repairs,
    }


async def _generate_initial_body(revision, plan, context_pack, generate_text):
    minimum, target, maximum = chapter_length_range(plan)
    prompt = chapter_prompt(
        context_pack=context_pack["context"],
        min_chars=minimum,
        target_chars=target,
        max_chars=maximum,
    )
    return await generate_text(revision, prompt, max_tokens=chapter_output_tokens(plan))


async def _generate_repaired_body(
    revision, plan, context_pack, evaluated, prior, generate_text
):
    minimum, target, maximum = chapter_length_range(plan)
    contract = prompt_chapter_contract(plan)
    violations = evaluated["state_validation"]["violations"]
    event_ids = contract.get("required_event_ids") or []
    timeline_ids = contract.get("canon_refs") or []
    prompt = chapter_gate_repair_prompt(
        context_pack=context_pack["context"],
        prior_result=(
            prior
            if evaluated["result"]
            and repair.can_reuse_prior_result(
                violations,
                current_event_ids=event_ids,
                current_timeline_ids=timeline_ids,
            )
            else None
        ),
        actual_chars=evaluated["actual_chars"],
        target_chars=target,
        violations=repair.repair_guidance(
            violations,
            current_event_ids=event_ids,
            current_timeline_ids=timeline_ids,
        ),
        min_chars=minimum,
        max_chars=maximum,
    )
    return await generate_text(
        revision,
        prompt,
        max_tokens=chapter_output_tokens(plan),
        temperature=0.2,
    )


async def _evaluate(
    revision, text: str, *, chapter_plan: dict, context_pack: dict, generate_text
) -> dict:
    result, parse_error = parse_chapter(text)
    actual_chars = non_whitespace_chars((result or {}).get("content_text", ""))
    min_chars, _target_chars, max_chars = chapter_length_range(chapter_plan)
    violations = []
    if not result:
        violations.append({"code": "canon_violation", "message": parse_error})
    elif not min_chars <= actual_chars <= max_chars:
        violations.append(
            {
                "code": "canon_violation",
                "message": f"章节长度为 {actual_chars}，要求 {min_chars}–{max_chars}",
            }
        )
    if result:
        violations.extend(
            required_event_anchor_violations(
                result["content_text"], prompt_chapter_contract(chapter_plan)
            )
        )
    delta, extraction_repairs, state_after, evidence_only = None, 0, None, False
    if result:
        violations.extend(
            premature_plan_violations(
                revision, int(chapter_plan["position"]), result["content_text"]
            )
        )
        violations.extend(
            revision_prose_canon_violations(
                revision, chapter_plan, result["content_text"]
            )
        )
    if result and not violations:
        try:
            (
                delta,
                extraction_repairs,
                state_after,
                state_violations,
            ) = await extract_and_validate_chapter_state(
                revision,
                result,
                chapter_plan,
                context_pack,
                generate_text,
            )
            violations.extend(state_violations)
        except StateExtractionError as exc:
            extraction_repairs = exc.repair_count
            evidence_only = exc.evidence_only
            violations.append({"code": "canon_violation", "message": str(exc)})
        except ValueError as exc:
            violations.append({"code": "canon_violation", "message": str(exc)})
    validation = {
        "status": "failed" if violations else "passed",
        "violations": violations,
    }
    return {
        "passed": not violations,
        "result": result,
        "parse_error": parse_error,
        "actual_chars": actual_chars,
        "state_delta": delta,
        "state_validation": validation,
        "state_after": state_after,
        "state_extraction_repair_count": extraction_repairs,
        "state_extraction_evidence_only": evidence_only,
        "validated_plot_delta": (
            validated_plot_delta(chapter_plan, delta) if delta else None
        ),
    }


async def extract_and_validate_chapter_state(
    revision, result, chapter_plan, context_pack, generate_text
):
    contract = prompt_chapter_contract(chapter_plan)
    canon = (revision.generation_plan or {}).get("canon") or {}
    timeline_ids = set(contract.get("canon_refs") or [])
    current_timeline = [
        item for item in canon.get("timeline") or [] if item.get("id") in timeline_ids
    ]
    delta, repairs = await extract_chapter_state(
        revision,
        chapter_plan=contract,
        state_before=context_pack["state_before"],
        content_text=result["content_text"],
        future_event_catalog=future_event_catalog(
            revision, int(chapter_plan["position"])
        ),
        current_timeline=current_timeline,
        canon=canon,
        generate_text=generate_text,
    )
    report, state_after = validate_state_delta(
        canon,
        contract,
        context_pack["state_before"],
        delta,
    )
    violations = [
        *report["violations"],
        *evidence_violations(result["content_text"], delta),
        *timeline_evidence_violations(result["content_text"], canon, contract, delta),
    ]
    return delta, repairs, state_after, violations
