"""Reconcile durable audit reservations before a v3 checkpoint."""

from app.repositories.llm_invocation_repository import LLMInvocationRepository
from sqlalchemy.orm import Session

from .story_novel_invocation_evidence import invocation_row_evidence
from .story_novel_v3_audit_budget import audit_contract_hash, require_audit_budget


def reservation_metrics(db, revision_business_id: str, entry: dict) -> dict:
    reservations = entry.get("audit_reservations") or []
    if not reservations:
        return {"attempts": [], "reservations": [], "complete": False}
    prefix = f"story_novel.{revision_business_id}.audit"
    invocation_db = Session(bind=db.get_bind())
    try:
        rows = LLMInvocationRepository(invocation_db).list_by_call_scene_prefix(prefix)
    finally:
        invocation_db.close()
    by_scene: dict[str, list] = {}
    for row in rows:
        by_scene.setdefault(row.call_scene, []).append(row)
    attempts = []
    resolved = []
    for reservation in reservations:
        scene = f"story_novel.{revision_business_id}.{reservation['stage']}"
        scene_rows = by_scene.get(scene) or []
        accepted = [
            row
            for row in scene_rows
            if row.status == "succeeded"
            and (row.response_metadata or {}).get("product_status", "accepted")
            == "accepted"
        ]
        item = dict(reservation)
        item["invocation_ids"] = [int(row.id) for row in scene_rows]
        if len(accepted) == 1:
            item.update(status="succeeded", accepted_invocation_id=int(accepted[0].id))
            attempts.append(invocation_row_evidence(accepted[0]))
        elif scene_rows and all(row.status != "processing" for row in scene_rows):
            item["status"] = "failed"
        else:
            item["status"] = "incomplete"
        resolved.append(item)
    return {
        "attempts": attempts,
        "reservations": resolved,
        "complete": all(item["status"] in {"succeeded", "failed"} for item in resolved),
    }


def prepare_checkpoint_audit(
    db,
    revision_business_id: str,
    position: int,
    entry: dict,
    candidate_body_hash: str,
    expected_delta: dict,
    merged_metrics: dict,
) -> tuple[str, str, dict]:
    from .story_novel_v3_generation import merge_stage_metrics

    contract_hash = audit_contract_hash(candidate_body_hash, expected_delta, entry)
    recovered = reservation_metrics(db, revision_business_id, entry)
    entry["audit_reservations"] = recovered["reservations"]
    if not recovered["complete"]:
        raise ValueError("审计 reservation 缺少明确终态调用证据")
    observed_ids = {
        item.get("invocation_id")
        for item in (merged_metrics.get("audit") or {}).get("attempts") or []
    }
    if not any(
        item.get("invocation_id") in observed_ids
        and f".body.{contract_hash}." in str(item.get("call_scene") or "")
        for item in recovered["attempts"]
    ):
        raise ValueError("最终正文缺少成功且匹配的审计调用证据")
    merged_metrics["audit"] = merge_stage_metrics(recovered)
    budget_hash = str(entry.get("audit_budget_hash") or contract_hash)
    candidate = {
        **entry,
        "audit_contract_hash": contract_hash,
        "stage_metrics": merged_metrics,
    }
    require_audit_budget(db, revision_business_id, position, candidate, budget_hash)
    return contract_hash, budget_hash, merged_metrics
