"""Additional approval requirements for generation-plan v3."""

import re

from app.services.narrative_memory.source_hash import novel_chapter_source_hash
from fastapi import HTTPException

from .story_novel_chapter_brief_contract import validate_chapter_brief
from .story_novel_context_utils import prompt_chapter_contract, value_hash
from .story_novel_expected_delta import compile_expected_delta
from .story_novel_planning_invocations import valid as valid_planning_invocations
from .story_novel_prose_length_control import valid_length_control
from .story_novel_prose_length_policy import valid_length_control_policy
from .story_novel_sentence_spans import (
    resolve_sentence_refs,
    sentence_index_hash,
    sentence_spans,
)
from .story_novel_state_service import (
    apply_state_delta,
    initial_story_state,
    state_hash,
)
from .story_novel_v3_audit import audit_contracts
from .story_novel_v3_context import build_v3_planning_context
from .story_novel_v3_invocation_gate import persisted_invocation_issues
from .story_novel_v3_prose_input import build_v3_prose_input
from .story_novel_v3_stage_evidence import valid_invocation, valid_stage_metrics


def require_v3_quality(db, revision, chapters, ledger_rows) -> None:
    plan = revision.generation_plan or {}
    if not valid_planning_invocations(plan):
        raise HTTPException(status_code=409, detail="v3 规划 invocation 证据不完整")
    if not valid_length_control_policy(db, revision):
        raise HTTPException(status_code=409, detail="v3 正文长度控制策略证据不完整")
    rows = {int(item["position"]): item for item in plan.get("chapters") or []}
    state = initial_story_state(plan.get("canon") or {})
    invalid = []
    for chapter in chapters:
        entry = ledger_rows.get(str(chapter.position)) or {}
        row = rows.get(chapter.position) or {}
        issues = _entry_issues(db, revision, chapter, row, entry, state)
        if issues:
            invalid.append({"position": chapter.position, "issues": issues})
        if entry.get("state_delta"):
            state = apply_state_delta(state, entry["state_delta"])
    if invalid:
        raise HTTPException(
            status_code=409,
            detail=f"v3 质量/hash/调用证据门禁不完整: {invalid}",
        )
    review = revision.continuity_report or {}
    invocations = review.get("review_invocations") or []
    audit_model = (plan.get("model_policy") or {}).get("audit_model")
    expected_reviews = (len(chapters) + 5) // 6 + 1
    if len(invocations) != expected_reviews or any(
        not valid_invocation(item, audit_model, require_prompt_template=True)
        for item in invocations
    ):
        raise HTTPException(status_code=409, detail="v3 连续性审读调用证据不完整")
    invocation_issues = persisted_invocation_issues(db, revision, ledger_rows, review)
    if invocation_issues:
        raise HTTPException(
            status_code=409,
            detail=f"v3 持久化 invocation 证据不完整: {invocation_issues}",
        )


def _entry_issues(db, revision, chapter, row, entry, state_before) -> list[str]:
    plan = revision.generation_plan or {}
    issues = _context_issues(db, revision, row, entry, state_before)
    expected = compile_expected_delta(row, state_before) if row else {}
    brief = dict(entry.get("chapter_brief") or {})
    if entry.get("expected_delta") != expected:
        issues.append("expected delta")
    if (
        entry.get("body_hash") != chapter.content_hash
        or entry.get("source_hash") != novel_chapter_source_hash(chapter)
        or not _valid_blocks(chapter.content_text, brief, entry.get("blocks") or [])
    ):
        issues.append("body/block/source hash")
    proofs = entry.get("proof_spans") or []
    required = {
        item["contract_id"]
        for item in audit_contracts(expected, plan.get("canon") or {}, row)
    }
    if {item.get("contract_id") for item in proofs} != required or not _valid_proofs(
        chapter.content_text, proofs, entry
    ):
        issues.append("proof/sentence hash")
    audit = entry.get("future_audit") or {}
    if any(
        audit.get(key)
        for key in ("future_hits", "unexpected_claims", "world_rule_hits")
    ):
        issues.append("future/world audit")
    if not valid_stage_metrics(db, revision, chapter.position, entry):
        issues.append("model invocation evidence")
    return issues


def _context_issues(db, revision, row, entry, state_before) -> list[str]:
    plan = revision.generation_plan or {}
    brief_input = dict(entry.get("brief_input") or {})
    brief = dict(entry.get("chapter_brief") or {})
    try:
        contract = prompt_chapter_contract(row)
        expected_delta = compile_expected_delta(contract, state_before)
        rebuilt = build_v3_planning_context(
            db,
            revision,
            int(row["position"]),
            row,
            persist_memory_snapshots=False,
        )
        rebuilt_input = rebuilt["brief_input"]
        validated = validate_chapter_brief(brief, brief_input)
        prose_input = build_v3_prose_input(
            rebuilt,
            validated,
            row,
        )
    except (KeyError, TypeError, ValueError):
        return ["brief/context/Canon hash"]
    length_valid = valid_length_control(
        db,
        revision,
        int(row["position"]),
        prose_input,
        (entry.get("stage_metrics") or {}).get("prose") or {},
    )
    valid = bool(
        brief_input == rebuilt_input
        and entry.get("context_evidence") == rebuilt["evidence"]
        and brief_input.get("chapter_contract") == contract
        and brief_input.get("chapter_contract_hash") == value_hash(contract)
        and brief_input.get("state_before") == state_before
        and brief_input.get("state_before_hash") == state_hash(state_before)
        and brief_input.get("expected_delta") == expected_delta
        and entry.get("brief_hash") == validated["brief_hash"]
        and entry.get("brief_input_hash") == value_hash(brief_input)
        and entry.get("context_hash") == value_hash(brief_input)
        and entry.get("chapter_contract_hash") == value_hash(contract)
        and entry.get("state_before_hash") == state_hash(state_before)
        and entry.get("canon_hash") == plan.get("canon_hash")
        and entry.get("prose_context_hash") == value_hash(prose_input)
    )
    issues = [] if valid else ["brief/context/Canon hash"]
    if not length_valid:
        issues.append("持久化 invocation/正文长度证据")
    return issues


def _valid_blocks(content: str, brief: dict, blocks: list[dict]) -> bool:
    if len(blocks) != len(brief.get("beats") or []):
        return False
    cursor = 0
    for index, item in enumerate(blocks, start=1):
        if item.get("block_id") != f"B{index:02d}" or item.get("start") != cursor:
            return False
        end = int(item.get("end") or -1)
        text = content[cursor:end]
        if (
            end <= cursor
            or item.get("content_hash") != value_hash(text)
            or item.get("char_count") != len(re.sub(r"\s+", "", text))
        ):
            return False
        cursor = end + (2 if index < len(blocks) else 0)
    return cursor == len(content)


def _valid_proofs(content: str, proofs: list[dict], entry: dict) -> bool:
    rows = sentence_spans(content)
    if entry.get("sentence_index_hash") != sentence_index_hash(rows):
        return False
    try:
        for proof in proofs:
            resolved = resolve_sentence_refs(
                content,
                proof["sentence_ids"],
                expected_source_hash=proof["source_hash"],
            )
            if any(resolved[key] != proof.get(key) for key in resolved):
                return False
    except (KeyError, TypeError, ValueError):
        return False
    return True
