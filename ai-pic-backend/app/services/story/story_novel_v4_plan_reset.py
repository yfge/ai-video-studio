"""Reset only stale v4 chapter contracts while preserving the frozen roadmap."""

from __future__ import annotations

from . import story_novel_planning_invocations as planning_invocations
from .story_novel_future_guard_index import compile_future_guard_index
from .story_novel_incremental_plan import chapter_skeleton, skeleton_hash
from .story_novel_length_service import generation_plan_hash
from .story_novel_world_reveal import compile_world_reveal_index


def reset_v4_plan_from(plan: dict, position: int) -> dict:
    """Discard derived contracts at and after position; keep Series Bible/Roadmap."""
    result = dict(plan)
    rows = []
    for source in result.get("chapters") or []:
        row_position = int(source["position"])
        if row_position < position:
            rows.append(dict(source))
            continue
        rows.append(
            {
                **chapter_skeleton(source),
                "preconditions": [],
                "state_transitions": [],
                "knowledge_grants": [],
                "location_transitions": [],
                "execution_contracts": [],
                "contract_status": "pending",
            }
        )
    result["chapters"] = rows
    result["compiled_chapter_count"] = max(0, position - 1)
    result["chapter_skeleton_hash"] = skeleton_hash(rows)
    future = compile_future_guard_index(
        rows,
        milestones=(result.get("canon") or {}).get("milestones") or [],
        entities=(result.get("canon") or {}).get("entities") or [],
    )
    reveal = compile_world_reveal_index(result.get("canon") or {}, rows)
    result.update(
        future_guard_index=future,
        future_guard_hash=future["index_hash"],
        world_reveal_index=reveal,
        world_reveal_hash=reveal["index_hash"],
    )
    manifest = dict(result.get("planning_invocations") or {})
    manifest["entries"] = [
        item
        for item in manifest.get("entries") or []
        if not _reset_package(item, position)
    ]
    planning_invocations.finalize(
        result,
        result.get("canon") or {},
        rows,
        source_manifest=manifest,
    )
    result["plan_hash"] = generation_plan_hash(result)
    return result


def mark_snapshot_stale(service, revision, position: int, reason: str) -> None:
    ledger = dict(revision.continuity_ledger or {})
    chapters = dict(ledger.get("chapters") or {})
    entry = dict(chapters.get(str(position)) or {})
    entry.update(
        status="snapshot_stale",
        stage="snapshot_stale",
        snapshot_stale_reason=reason,
    )
    chapters[str(position)] = entry
    stale = min(int(ledger.get("stale_from_position") or position), position)
    ledger.update(chapters=chapters, state_status="stale", stale_from_position=stale)
    revision.continuity_ledger = ledger
    service._invalidate_from(revision, position)
    service.db.commit()


def reset_stale_snapshot_suffix(revision, start_position: int) -> int | None:
    entries = (revision.continuity_ledger or {}).get("chapters") or {}
    stale = [
        int(key)
        for key, entry in entries.items()
        if int(key) >= start_position
        and entry.get("status") in {"snapshot_stale", "gate_failed"}
    ]
    if not stale:
        return None
    position = min(stale)
    revision.generation_plan = reset_v4_plan_from(
        revision.generation_plan or {}, position
    )
    ledger = dict(revision.continuity_ledger or {})
    chapters = dict(ledger.get("chapters") or {})
    for key in list(chapters):
        if int(key) >= position:
            chapters.pop(key)
    ledger.update(chapters=chapters, state_status="stale", stale_from_position=position)
    revision.continuity_ledger = ledger
    return position


def _reset_package(entry: dict, position: int) -> bool:
    stage = str(entry.get("logical_stage") or "")
    if not stage.startswith("chapter_package."):
        return False
    return any(int(value) >= position for value in entry.get("positions") or [])
