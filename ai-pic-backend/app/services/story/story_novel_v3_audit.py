"""Proof-only audit and deterministic state promotion for v3 chapters."""

from __future__ import annotations

import copy

from app.services.narrative_memory.knowledge_evidence import knowledge_evidence_key
from app.utils.json_utils import extract_json_block

from .story_novel_sentence_spans import (
    resolve_sentence_refs,
    sentence_index_hash,
    sentence_spans,
)
from .story_novel_state_validator import validate_state_delta
from .story_novel_v3_proof_validation import (
    normalize_source_bound_proofs,
    source_bound_proof_violations,
)
from .story_novel_v3_repair_guidance import repair_issues

_AUDIT_KEYS = {"proofs", "unexpected_claims", "future_hits", "world_rule_hits"}


def audit_contracts(
    expected_delta: dict, canon: dict, chapter_plan: dict
) -> list[dict]:
    # Timeline is evaluated semantically from current_timeline; it is not a
    # second source-proof contract and never requires a literal date sentence.
    contracts = [copy.deepcopy(item) for item in expected_delta["proof_contracts"]]
    ids = [item["contract_id"] for item in contracts]
    if len(ids) != len(set(ids)):
        raise ValueError("audit proof contract ID 重复")
    return contracts


def parse_proof_audit(text: str, contracts: list[dict], content_text: str) -> dict:
    payload = extract_json_block(text)
    if not isinstance(payload, dict) or set(payload) != _AUDIT_KEYS:
        raise ValueError("audit 只能包含 proofs 与三类 issue")
    proofs = list(payload.get("proofs") or [])
    contract_ids = {item["contract_id"] for item in contracts}
    supplied = [item.get("contract_id") for item in proofs]
    if (
        len(supplied) != len(set(supplied))
        or not set(supplied).issubset(contract_ids)
        or any(set(item) != {"contract_id", "sentence_ids"} for item in proofs)
    ):
        raise ValueError("audit proofs 包含重复、未知或越界结构")
    resolved = []
    for proof in proofs:
        evidence = resolve_sentence_refs(content_text, proof["sentence_ids"])
        resolved.append({**proof, **evidence})
    issues = {
        key: _issue_rows(payload.get(key), key, content_text)
        for key in ("unexpected_claims", "future_hits", "world_rule_hits")
    }
    if any(item.get("claim_id") for item in issues["unexpected_claims"]):
        raise ValueError("future claim 必须归入 future_hits")
    if any(not item.get("claim_id") for item in issues["future_hits"]):
        raise ValueError("future_hits 必须绑定 claim_id")
    return {
        "proofs": resolved,
        "missing_proof_contracts": sorted(contract_ids - set(supplied)),
        **issues,
    }


def evaluate_proof_audit(
    *,
    audit: dict,
    expected_delta: dict,
    canon: dict,
    chapter_plan: dict,
    state_before: dict,
    content_text: str,
    brief: dict,
    block_manifest: list[dict],
) -> dict:
    proofs = {
        item["contract_id"]: item
        for item in normalize_source_bound_proofs(audit["proofs"], expected_delta)
    }
    delta = _delta_with_evidence(expected_delta, proofs, chapter_plan)
    report, state_after = validate_state_delta(canon, chapter_plan, state_before, delta)
    state_violations = list(report["violations"])
    missing_violations = [
        {
            "code": "proof_missing",
            "message": f"正文缺少合同证明: {contract_id}",
        }
        for contract_id in audit.get("missing_proof_contracts") or []
    ]
    proof_violations, content_proof_failure = source_bound_proof_violations(
        proofs, expected_delta, canon, chapter_plan, content_text
    )
    model_violations = []
    for key, reason_code in (
        ("unexpected_claims", "unexpected_claim"),
        ("future_hits", "future_hit"),
        ("world_rule_hits", "world_rule_hit"),
    ):
        model_violations.extend(
            {
                "code": "canon_violation",
                "reason_code": reason_code,
                "message": str(item.get("message") or item),
            }
            for item in audit.get(key) or []
        )
    evidence_only = bool(
        (missing_violations or proof_violations)
        and not state_violations
        and not model_violations
        and not content_proof_failure
    )
    violations = [
        *state_violations,
        *missing_violations,
        *proof_violations,
        *model_violations,
    ]
    failed = _failed_blocks(violations, audit, proofs, brief, block_manifest)
    index = sentence_spans(content_text)
    return {
        "passed": not violations,
        "state_delta": delta,
        "state_after": state_after,
        "state_validation": {
            "status": "passed" if not violations else "failed",
            "violations": violations,
        },
        "proof_spans": list(proofs.values()),
        "sentence_index": index,
        "sentence_index_hash": sentence_index_hash(index),
        "failed_block_ids": failed,
        "repair_issues": [
            *repair_issues(audit),
        ],
        "repairable": bool(model_violations or content_proof_failure)
        and not state_violations,
        "state_contract_failed": bool(state_violations),
        "failure_kind": "evidence_only" if evidence_only else "content",
        "future_audit": {
            "unexpected_claims": audit.get("unexpected_claims") or [],
            "future_hits": audit.get("future_hits") or [],
            "world_rule_hits": audit.get("world_rule_hits") or [],
        },
    }


def _delta_with_evidence(expected, proofs, chapter_plan) -> dict:
    delta = {
        key: copy.deepcopy(value)
        for key, value in expected.items()
        if key not in {"proof_contracts", "delta_hash", "schema"}
    }
    delta["evidence"] = {
        event_id: proofs[f"event:{event_id}"]["quote"]
        for event_id in delta.get("occurred_event_ids") or []
        if f"event:{event_id}" in proofs
    }
    delta["knowledge_evidence"] = {
        knowledge_evidence_key(item): proofs[f"knowledge:{index}"]["quote"]
        for index, item in enumerate(delta.get("knowledge_grants") or [], start=1)
        if f"knowledge:{index}" in proofs
    }
    delta["timeline_evidence"] = {
        timeline_id: proofs[f"timeline:{timeline_id}"]["quote"]
        for timeline_id in (chapter_plan.get("timeline_event_bindings") or {})
        if f"timeline:{timeline_id}" in proofs
    }
    delta["premature_future_event_ids"] = []
    delta["world_rule_violations"] = []
    return delta


def _issue_rows(value, label: str, content_text: str) -> list[dict]:
    rows = list(value or [])
    result = []
    for item in rows:
        allowed = {"message", "sentence_ids", "claim_id", "rule_id"}
        if (
            isinstance(item, dict)
            and not set(item).difference(allowed)
            and str(item.get("message") or "").strip()
            and item.get("sentence_ids")
        ):
            row = dict(item)
            row.update(resolve_sentence_refs(content_text, row["sentence_ids"]))
            result.append(row)
        else:
            raise ValueError(f"{label} issue 结构无效")
    return result


def _failed_blocks(violations, audit, proofs, brief, blocks) -> list[str]:
    failed = set()
    for item in [
        *audit.get("unexpected_claims", []),
        *audit.get("future_hits", []),
        *audit.get("world_rule_hits", []),
    ]:
        failed.update(_blocks_for_spans(item.get("spans") or [], blocks))
    messages = " ".join(str(item.get("message") or "") for item in violations)
    for beat in brief.get("beats") or []:
        if any(
            contract_id in messages
            for contract_id in beat.get("effect_contract_ids") or []
        ):
            failed.add(beat["beat_id"])
    if not failed and violations:
        failed.add((brief.get("beats") or [{"beat_id": "B01"}])[-1]["beat_id"])
    return sorted(failed)


def _blocks_for_spans(spans, blocks) -> set[str]:
    return {
        block["block_id"]
        for span in spans
        for block in blocks
        if span["start"] < block["end"] and span["end"] > block["start"]
    }
