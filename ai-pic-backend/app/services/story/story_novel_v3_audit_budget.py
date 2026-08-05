"""Hash-bound substantive audit budget for one immutable v3 body."""

import uuid

from app.models.task import TaskStatus
from app.repositories.llm_invocation_repository import LLMInvocationRepository

from .story_novel_v3_audit_contract import audit_contract_hash as audit_contract_hash
from .story_novel_v3_audit_reservation_state import reservation_transport_counts

MAX_AUDIT_ATTEMPTS_PER_BODY = 3
MAX_AUDIT_TRANSPORT_FAILURES_PER_BODY = 3


def consumed_audit_attempts(entry: dict, contract_hash: str) -> int:
    stored_hash = entry.get("audit_budget_hash") or entry.get("audit_contract_hash")
    if stored_hash != contract_hash:
        return 0
    metric = (entry.get("stage_metrics") or {}).get("audit") or {}
    reservations = entry.get("audit_reservations") or []
    succeeded = sum(1 for item in reservations if item.get("status") == "succeeded")
    return max(len(metric.get("attempts") or []), succeeded)


def audit_stage(position: int, contract_hash: str) -> str:
    return f"audit.{position}.{contract_hash}"


def persisted_audit_attempts(
    db, revision_business_id: str, position: int, contract_hash: str
) -> int:
    prefix = (
        f"story_novel.{revision_business_id}.{audit_stage(position, contract_hash)}"
    )
    rows = LLMInvocationRepository(db).list_by_call_scene_prefix(prefix)
    return len(
        {
            row.call_scene
            for row in rows
            if row.status == "succeeded"
            and (row.response_metadata or {}).get("product_status", "accepted")
            == "accepted"
        }
    )


def audit_budget_available(
    entry: dict, contract_hash: str, persisted_attempts: int = 0
) -> int:
    consumed = max(
        consumed_audit_attempts(entry, contract_hash), int(persisted_attempts or 0)
    )
    return max(
        0,
        MAX_AUDIT_ATTEMPTS_PER_BODY - consumed,
    )


def require_audit_budget(
    db, revision_business_id: str, position: int, entry: dict, contract_hash: str
) -> None:
    persisted = persisted_audit_attempts(
        db, revision_business_id, position, contract_hash
    )
    if (
        max(consumed_audit_attempts(entry, contract_hash), persisted)
        > MAX_AUDIT_ATTEMPTS_PER_BODY
    ):
        raise ValueError("当前正文审计调用次数超过硬上限")


def reserve_audit_attempt(
    service,
    revision,
    entry: dict,
    position: int,
    budget_hash: str,
    logical_stage: str,
    *,
    task_id: int | None,
) -> str:
    locked = service.repo.revision_by_id(revision.id, for_update=True)
    if locked is None:
        raise ValueError("小说 Revision 不存在，无法预留审计额度")
    ledger = dict(locked.continuity_ledger or {})
    chapters = dict(ledger.get("chapters") or {})
    live_entry = dict(chapters.get(str(position)) or {})
    stored_hash = live_entry.get("audit_budget_hash") or live_entry.get(
        "audit_contract_hash"
    )
    if stored_hash != budget_hash:
        raise ValueError("审计预算链已变化，拒绝调用模型")
    reservations = _without_abandoned(
        service,
        revision.business_id,
        position,
        budget_hash,
        list(live_entry.get("audit_reservations") or []),
        task_id,
    )
    active, transport_failed = reservation_transport_counts(
        service, revision.business_id, position, budget_hash, reservations, task_id
    )
    used = max(
        consumed_audit_attempts(live_entry, budget_hash),
        persisted_audit_attempts(
            service.db, revision.business_id, position, budget_hash
        ),
    )
    if used + active >= MAX_AUDIT_ATTEMPTS_PER_BODY:
        raise ValueError("当前正文审计调用预算已耗尽")
    if transport_failed >= MAX_AUDIT_TRANSPORT_FAILURES_PER_BODY:
        raise ValueError("当前正文审计传输失败次数已耗尽")
    reservation_id = f"r{len(reservations) + 1:02d}-{uuid.uuid4().hex[:12]}"
    stage = f"{logical_stage}.{reservation_id}"
    reservations.append(
        {
            "reservation_id": reservation_id,
            "budget_hash": budget_hash,
            "stage": stage,
            "task_id": task_id,
            "status": "reserved",
        }
    )
    live_entry.update(
        audit_budget_hash=budget_hash,
        audit_reservations=reservations,
    )
    chapters[str(position)] = live_entry
    ledger["chapters"] = chapters
    locked.continuity_ledger = ledger
    service.db.commit()
    entry.update(
        audit_budget_hash=budget_hash,
        audit_reservations=reservations,
    )
    return stage


def prune_abandoned_reservations(
    service,
    revision,
    entry: dict,
    position: int,
    budget_hash: str,
    task_id: int | None,
) -> None:
    locked = service.repo.revision_by_id(revision.id, for_update=True)
    if locked is None:
        raise ValueError("小说 Revision 不存在，无法恢复审计预算")
    ledger = dict(locked.continuity_ledger or {})
    chapters = dict(ledger.get("chapters") or {})
    live_entry = dict(chapters.get(str(position)) or {})
    before = list(live_entry.get("audit_reservations") or [])
    reservations = _without_abandoned(
        service,
        revision.business_id,
        position,
        budget_hash,
        before,
        task_id,
    )
    if reservations != before:
        live_entry["audit_reservations"] = reservations
        chapters[str(position)] = live_entry
        ledger["chapters"] = chapters
        locked.continuity_ledger = ledger
        service.db.commit()
    else:
        service.db.rollback()
    entry["audit_reservations"] = reservations


def lock_checkpoint_entry(service, revision, position: int, entry: dict):
    locked = service.repo.revision_by_id(revision.id, for_update=True)
    if locked is None:
        raise ValueError("小说 Revision 不存在，无法 checkpoint")
    live = dict(
        ((locked.continuity_ledger or {}).get("chapters") or {}).get(str(position))
        or {}
    )
    chain_fields = (
        "body_hash",
        "audit_budget_hash",
        "audit_contract_hash",
        "chapter_contract_hash",
        "context_hash",
        "canon_hash",
        "state_before_hash",
    )
    if any(live.get(key) != entry.get(key) for key in chain_fields):
        raise ValueError("章节正文或上下文链已变化，拒绝旧 worker checkpoint")
    entry["audit_reservations"] = list(live.get("audit_reservations") or [])
    return locked


def _without_abandoned(
    service,
    revision_business_id: str,
    position: int,
    budget_hash: str,
    reservations: list[dict],
    current_task_id: int | None,
) -> list[dict]:
    prefix = f"story_novel.{revision_business_id}.{audit_stage(position, budget_hash)}"
    scenes = {
        row.call_scene
        for row in LLMInvocationRepository(service.db).list_by_call_scene_prefix(prefix)
    }
    kept = []
    for item in reservations:
        scene = f"story_novel.{revision_business_id}.{item.get('stage')}"
        owner_id = item.get("task_id")
        owner = service.repo.task(int(owner_id)) if owner_id else None
        owner_active = owner and owner.status in {
            TaskStatus.PENDING,
            TaskStatus.PROCESSING,
        }
        if scene in scenes or owner_id == current_task_id or owner_active:
            kept.append(item)
    return kept
