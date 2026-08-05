"""Versioned audit-input contract and checkpoint-safe upgrades."""

from .story_novel_context_utils import value_hash

AUDIT_INPUT_VERSION = 5
AUDIT_VALIDATION_VERSION = 2
_CHAIN_FIELDS = (
    "body_hash",
    "chapter_contract_hash",
    "context_hash",
    "canon_hash",
    "state_before_hash",
)


def audit_contract_hash(body_hash: str, expected_delta: dict, entry: dict) -> str:
    return value_hash(
        {
            "audit_input_version": AUDIT_INPUT_VERSION,
            "audit_validation_version": AUDIT_VALIDATION_VERSION,
            "body_hash": body_hash,
            "expected_delta_hash": expected_delta.get("delta_hash"),
            "chapter_contract_hash": entry.get("chapter_contract_hash"),
            "canon_hash": entry.get("canon_hash"),
            "context_hash": entry.get("context_hash"),
        }
    )


def ensure_audit_contract(
    service,
    revision,
    entry: dict,
    position: int,
    contract_hash: str,
) -> str:
    """Upgrade an old prompt contract without changing its immutable body chain."""
    if entry.get("audit_contract_hash") == contract_hash:
        return str(entry.get("audit_budget_hash") or contract_hash)
    locked = service.repo.revision_by_id(revision.id, for_update=True)
    if locked is None:
        raise ValueError("小说 Revision 不存在，无法升级审计合同")
    ledger = dict(locked.continuity_ledger or {})
    chapters = dict(ledger.get("chapters") or {})
    live = dict(chapters.get(str(position)) or {})
    if live.get("audit_contract_hash") == contract_hash:
        entry.update(live)
        service.db.rollback()
        return str(live.get("audit_budget_hash") or contract_hash)
    if any(live.get(key) != entry.get(key) for key in _CHAIN_FIELDS):
        service.db.rollback()
        raise ValueError("章节正文或上下文链已变化，拒绝升级审计合同")
    history = list(live.get("audit_contract_history") or [])
    history.append(
        {
            "audit_contract_hash": live.get("audit_contract_hash"),
            "audit_budget_hash": live.get("audit_budget_hash"),
            "audit_reservations": list(live.get("audit_reservations") or []),
            "audit_metrics": (live.get("stage_metrics") or {}).get("audit"),
        }
    )
    metrics = dict(live.get("stage_metrics") or {})
    metrics.pop("audit", None)
    live.update(
        {
            "audit_input_version": AUDIT_INPUT_VERSION,
            "audit_validation_version": AUDIT_VALIDATION_VERSION,
            "audit_contract_hash": contract_hash,
            "audit_budget_hash": contract_hash,
            "audit_reservations": [],
            "audit_contract_history": history,
            "audit_failure_kind": None,
            "stage_metrics": metrics,
        }
    )
    chapters[str(position)] = live
    ledger["chapters"] = chapters
    locked.continuity_ledger = ledger
    service.db.commit()
    entry.update(live)
    return contract_hash
