"""Retain failed Arc calls as evidence without reusing their active stage keys."""

from __future__ import annotations


def archive_failed_arc_calls(entry: dict, arc_id: str) -> bool:
    active = dict(entry.get("model_call_snapshots") or {})
    prefix = f"arc_planning.{arc_id}"
    failed = [key for key in active if key == prefix or key.startswith(f"{prefix}.")]
    if not failed:
        return False
    archived = list(entry.get("failed_model_call_snapshots") or [])
    for key in sorted(failed):
        archived.append(
            {
                "logical_stage": key,
                "reason": "arc_plan_validation_failed",
                "snapshot": active.pop(key),
            }
        )
    entry["model_call_snapshots"] = active
    entry["failed_model_call_snapshots"] = archived
    return True


def archive_stale_arc_snapshot(entry: dict, arc_id: str, reason: str) -> bool:
    snapshot = entry.pop("arc_planner_snapshot", None)
    if not isinstance(snapshot, dict):
        return False
    archive_failed_arc_calls(entry, arc_id)
    archived = list(entry.get("stale_arc_planner_snapshots") or [])
    archived.append({"reason": reason, "snapshot": snapshot})
    entry["stale_arc_planner_snapshots"] = archived
    entry.pop("arc_planner_snapshot_hash", None)
    return True
