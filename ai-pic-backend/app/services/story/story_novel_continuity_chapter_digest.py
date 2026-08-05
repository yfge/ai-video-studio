"""Compact chapter and v4 plan evidence for whole-book review."""

from __future__ import annotations

import copy


def plan_binding(plan: dict) -> dict:
    return {
        key: copy.deepcopy(plan.get(key))
        for key in (
            "schema",
            "version",
            "plan_hash",
            "canon_hash",
            "outline_hash",
            "chapter_count",
            "target_chars",
            "model_policy",
            "planning_structure_version",
            "future_guard_hash",
            "series_bible_hash",
            "series_roadmap_hash",
            "arc_plans_hash",
            "scope_graph_hash",
            "planner_snapshot_schema",
            "chapter_intent_schema",
            "chapter_contract_schema",
            "audit_proof_schema",
        )
        if plan.get(key) is not None
    }


def progression_arcs(snapshot: dict) -> list[dict]:
    outline = (snapshot.get("story_seed") or {}).get("structured_outline") or {}
    return copy.deepcopy(outline.get("progression_arcs") or [])


def chapter_digest(chapter, ledger_rows: dict) -> dict:
    entry = ledger_rows.get(str(chapter.position)) or {}
    proofs = entry.get("proof_spans") or []
    proof_refs, evidence = _proof_digest(proofs)
    return {
        "business_id": chapter.business_id,
        "position": chapter.position,
        "title": str(chapter.title or ""),
        "summary": str(chapter.summary or ""),
        "cliffhanger": str(chapter.cliffhanger or ""),
        "content_hash": chapter.content_hash,
        "body_hash": entry.get("body_hash"),
        "source_hash": entry.get("source_hash"),
        "context_hash": entry.get("context_hash"),
        "canon_hash": entry.get("canon_hash"),
        "state_before_hash": entry.get("state_before_hash"),
        "state_after_hash": entry.get("state_after_hash"),
        "sentence_index_hash": entry.get("sentence_index_hash"),
        "planner_snapshot_hash": entry.get("planner_snapshot_hash"),
        "arc_planner_snapshot_hash": entry.get("arc_planner_snapshot_hash"),
        "chapter_intent_hash": entry.get("chapter_intent_hash"),
        "chapter_contract_hash": entry.get("chapter_contract_hash"),
        "model_call_snapshot_hashes": {
            key: item.get("snapshot_hash")
            for key, item in (entry.get("model_call_snapshots") or {}).items()
        },
        "entity_proposals": copy.deepcopy(
            (entry.get("chapter_intent") or {}).get("entity_proposals") or []
        ),
        "plot_delta": _compact(
            entry.get("plot_delta") or {},
            ("key_events", "unresolved_threads", "resolved_threads"),
        ),
        "state_delta": _compact(
            entry.get("state_delta") or {},
            (
                "occurred_event_ids",
                "state_transitions",
                "location_transitions",
                "knowledge_grants",
                "milestones_consumed",
                "opened_thread_ids",
                "resolved_thread_ids",
                "entity_introductions",
            ),
        ),
        "proof_refs": proof_refs,
        "sentence_index": evidence,
        "proof_manifest": {
            "proof_count": len(proofs),
            "source_sentence_ref_count": sum(
                len(item.get("sentence_ids") or []) for item in proofs
            ),
            "global_sentence_ref_count": sum(len(item) for item in proof_refs.values()),
            "selection_policy": "event_first_last_other_last",
        },
        "future_audit": copy.deepcopy(entry.get("future_audit") or {}),
    }


def _compact(value: dict, keys: tuple[str, ...]) -> dict:
    return {key: copy.deepcopy(value.get(key)) for key in keys if value.get(key)}


def _proof_digest(proofs: list[dict]) -> tuple[dict[str, list[str]], list[dict]]:
    refs = {}
    sentences: dict[str, str] = {}
    for proof in proofs:
        contract_id = str(proof.get("contract_id") or "")
        source_ids = [str(value) for value in proof.get("sentence_ids") or []]
        ids = _global_proof_ids(contract_id, source_ids)
        refs[contract_id] = ids
        for span in proof.get("spans") or []:
            sentence_id = str(span.get("sentence_id") or "")
            if sentence_id and sentence_id in ids:
                sentences.setdefault(sentence_id, str(span.get("text") or ""))
    return refs, [
        {"sentence_id": sentence_id, "text": text}
        for sentence_id, text in sentences.items()
    ]


def _global_proof_ids(contract_id: str, sentence_ids: list[str]) -> list[str]:
    if not sentence_ids:
        return []
    if contract_id.startswith("event:") and len(sentence_ids) > 1:
        return [sentence_ids[0], sentence_ids[-1]]
    return [sentence_ids[-1]]
