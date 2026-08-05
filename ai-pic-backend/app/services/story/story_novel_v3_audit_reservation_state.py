"""Classify durable audit reservations without consuming semantic budget."""

from app.models.task import TaskStatus
from app.repositories.llm_invocation_repository import LLMInvocationRepository


def reservation_transport_counts(
    service,
    revision_business_id,
    position,
    budget_hash,
    reservations,
    current_task_id,
):
    prefix = f"story_novel.{revision_business_id}.audit.{position}.{budget_hash}"
    rows = LLMInvocationRepository(service.db).list_by_call_scene_prefix(prefix)
    by_scene = {}
    for row in rows:
        by_scene.setdefault(row.call_scene, []).append(row)
    active = failed = 0
    for item in reservations:
        scene = f"story_novel.{revision_business_id}.{item.get('stage')}"
        scene_rows = by_scene.get(scene) or []
        accepted = any(
            row.status == "succeeded"
            and (row.response_metadata or {}).get("product_status", "accepted")
            == "accepted"
            for row in scene_rows
        )
        if accepted:
            continue
        if scene_rows:
            active += any(row.status == "processing" for row in scene_rows)
            failed += all(row.status != "processing" for row in scene_rows)
            continue
        owner_id = item.get("task_id")
        owner = service.repo.task(int(owner_id)) if owner_id else None
        active += bool(
            owner_id == current_task_id
            or owner
            and owner.status in {TaskStatus.PENDING, TaskStatus.PROCESSING}
        )
    return int(active), int(failed)
