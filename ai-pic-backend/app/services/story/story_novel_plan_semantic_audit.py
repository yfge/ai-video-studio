"""Independent event-by-event semantic audit for executable chapter plans."""

from copy import deepcopy

from app.utils.json_utils import extract_json_block

from . import story_novel_planning_invocations as planning_invocations
from .story_novel_canon_service import content_hash
from .story_novel_context_utils import prompt_chapter_contract, value_hash
from .story_novel_plan_execution_contract import (
    apply_execution_contracts,
    execution_issues,
    parse_plan_semantic_audit,
)
from .story_novel_plan_semantic_effects import (
    audit_has_effects,
    filter_redundant_audit_effects,
    remove_unsupported_effects,
)
from .story_novel_plan_semantic_prompt import EFFECT_FIELDS as _EFFECT_FIELDS
from .story_novel_plan_semantic_prompt import (
    build_plan_semantic_audit_prompt as _audit_prompt,
)
from .story_novel_plan_state_compiler import compile_plan_state
from .story_novel_plan_validator import validate_generation_plan
from .story_novel_planning_batches import validated_prefix_context

PLAN_SEMANTIC_AUDIT_VERSION, PLAN_SEMANTIC_AUDIT_MAX_TOKENS = 3, 16000
_parse_audit = parse_plan_semantic_audit


def requires_plan_semantic_audit(contract: dict) -> bool:
    seed = contract.get("story_seed") or {}
    return seed.get("schema") == "story_seed_v2" and bool(
        (seed.get("structured_outline") or {}).get("chapters")
    )


async def audit_and_patch_plan_batch(
    revision,
    *,
    contract: dict,
    canon: dict,
    prior_chapters: list[dict],
    batch_chapters: list[dict],
    require_complete: bool,
    generate_text,
) -> list[dict]:
    prompt = _audit_prompt(contract, canon, prior_chapters, batch_chapters)
    first_text = await generate_text(
        revision,
        prompt,
        max_tokens=PLAN_SEMANTIC_AUDIT_MAX_TOKENS,
        temperature=0.0,
    )
    first = filter_redundant_audit_effects(
        _parse_audit(first_text, canon, batch_chapters),
        canon,
        prior_chapters,
        batch_chapters,
    )
    _reject_blocking_execution_issues(first)
    patched, patch_count = _apply_missing_effects(batch_chapters, first)
    patched, removed = remove_unsupported_effects(patched, first)
    patch_count += removed
    patched = apply_execution_contracts(patched, first)
    patched = compile_plan_state(canon, [*prior_chapters, *patched])[
        len(prior_chapters) :
    ]
    candidate = [*prior_chapters, *patched]
    if require_complete:
        validate_generation_plan(canon, candidate)
    else:
        validated_prefix_context(canon, candidate)
    final_text, final = first_text, first
    if patch_count:
        final_text = await generate_text(
            revision,
            _audit_prompt(
                contract,
                canon,
                prior_chapters,
                patched,
                verification=True,
                verification_targets=first,
            ),
            max_tokens=PLAN_SEMANTIC_AUDIT_MAX_TOKENS,
            temperature=0.0,
        )
        final = filter_redundant_audit_effects(
            _parse_audit(final_text, canon, patched),
            canon,
            prior_chapters,
            patched,
        )
        _require_execution_stability(first, final)
        _reject_blocking_execution_issues(final)
        if audit_has_effects(final):
            raise ValueError("章节计划语义审计返修后仍存在 typed effect 漏项")
        patched = apply_execution_contracts(patched, final)
    result_hash = content_hash(extract_json_block(final_text))
    for chapter in patched:
        event_ids = list(chapter.get("required_event_ids") or [])
        chapter["semantic_audit"] = {
            "version": PLAN_SEMANTIC_AUDIT_VERSION,
            "status": "passed",
            "event_ids": event_ids,
            "contract_hash": _chapter_contract_hash(chapter),
            "result_hash": result_hash,
            "patched_effect_count": patch_count,
            "execution_contract_version": 1,
            "execution_advisories": [
                item
                for item in execution_issues(final, severity="advisory")
                if item["position"] == int(chapter["position"])
            ],
        }
    positions = [int(item["position"]) for item in batch_chapters]
    stage = f"semantic_audit.batch.{positions[0]}-{positions[-1]}"
    plan_result_hash = value_hash([prompt_chapter_contract(item) for item in patched])
    if patch_count:
        planning_invocations.record(
            revision,
            f"{stage}.initial",
            first_text,
            positions=positions,
            result_hash=plan_result_hash,
        )
        stage = f"{stage}.verification"
    planning_invocations.record(
        revision,
        stage,
        final_text,
        positions=positions,
        result_hash=plan_result_hash,
    )
    return patched


def _apply_missing_effects(chapters: list[dict], audit: list[dict]):
    patched = deepcopy(chapters)
    by_position = {int(item["position"]): item for item in patched}
    count = 0
    for event in audit:
        chapter = by_position[event["position"]]
        for field in _EFFECT_FIELDS:
            values = event["missing_effects"][field]
            target = chapter.setdefault(field, [])
            for value in values:
                if value not in target:
                    target.append(value)
                    count += 1
    return patched, count


def _reject_blocking_execution_issues(audit: list[dict]) -> None:
    issues = execution_issues(audit, severity="blocking")
    if not issues:
        return
    summary = "; ".join(
        f"第 {item['position']} 章 {item['event_id']} {item['code']}: {item['message']}"
        for item in issues[:5]
    )
    raise ValueError(f"章节计划不可执行: {summary}")


def _require_execution_stability(first: list[dict], final: list[dict]) -> None:
    keys = ("action_phase", "time_scope", "actor_ids", "effort")
    for before, after in zip(first, final, strict=True):
        old = before["execution_contract"]
        new = after["execution_contract"]
        if (
            any(old[key] != new[key] for key in keys)
            or before["feasibility_issues"] != after["feasibility_issues"]
        ):
            raise ValueError("章节计划语义审计返修后 execution contract 漂移")


def _chapter_contract_hash(chapter: dict) -> str:
    return content_hash({k: v for k, v in chapter.items() if k != "semantic_audit"})
