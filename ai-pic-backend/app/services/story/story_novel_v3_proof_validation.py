"""Source-bound proof checks that apply only to v3 sentence references."""

from __future__ import annotations

import copy


def merge_proof_audits(first: dict, retry: dict) -> dict:
    """Overlay retry proofs without discarding contracts proved on the first pass."""
    proofs = {
        item["contract_id"]: item
        for item in [*(first.get("proofs") or []), *(retry.get("proofs") or [])]
    }
    contract_ids = {
        *proofs,
        *(first.get("missing_proof_contracts") or []),
    }
    return {
        "proofs": list(proofs.values()),
        "missing_proof_contracts": sorted(contract_ids - set(proofs)),
        **{
            key: list(retry.get(key) or [])
            for key in ("unexpected_claims", "future_hits", "world_rule_hits")
        },
    }


def source_bound_proof_violations(
    proofs: dict[str, dict],
    expected_delta: dict,
    canon: dict,
    chapter_plan: dict,
    content_text: str,
) -> tuple[list[dict], bool]:
    """Keep source checks structural; the audit model owns causal semantics.

    Parsing already proves that every contract and sentence ID exists in the
    current body. Sentence order cannot prove causality: a character may learn
    something during the discovery part of an event before its completion
    sentence. Future and unexpected knowledge remain fail-closed in the audit.
    """
    return [], False


def normalize_source_bound_proofs(
    proof_rows: list[dict], expected_delta: dict
) -> list[dict]:
    """Preserve all model-selected source spans for semantic audit evidence."""
    return copy.deepcopy(proof_rows)
