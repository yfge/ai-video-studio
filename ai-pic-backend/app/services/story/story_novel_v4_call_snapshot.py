"""Persist exact immutable model-call inputs before v4 provider transport."""

from __future__ import annotations

from app.repositories.llm_invocation_repository import LLMInvocationRepository

from .story_novel_context_utils import value_hash
from .story_novel_invocation_evidence import GeneratedNovelText, invocation_row_evidence

SCHEMA = "story_novel_model_call_snapshot.v1"


def freeze_v4_call_input(
    service,
    revision,
    position: int,
    entry: dict,
    logical_stage: str,
    prompt: str,
    *,
    reuse_existing_input: bool = False,
) -> dict:
    locked = service.repo.revision_by_id(revision.id, for_update=True)
    if locked is None:
        raise ValueError("小说 Revision 不存在，无法冻结模型调用")
    ledger = dict(locked.continuity_ledger or {})
    chapters = dict(ledger.get("chapters") or {})
    live = dict(chapters.get(str(position)) or {})
    snapshot = {
        "schema": SCHEMA,
        "position": position,
        "logical_stage": logical_stage,
        "normalized_input": str(prompt),
        "input_hash": value_hash(str(prompt)),
        "planner_snapshot_hash": live.get("planner_snapshot_hash"),
        "arc_planner_snapshot_hash": live.get("arc_planner_snapshot_hash"),
        "chapter_intent_hash": live.get("chapter_intent_hash"),
        "chapter_contract_hash": live.get("chapter_contract_hash"),
        "execution_generation_plan_hash": live.get("execution_generation_plan_hash"),
        "canon_hash": live.get("canon_hash"),
        "state_before_hash": live.get("state_before_hash"),
        "body_hash": entry.get("body_hash", live.get("body_hash")),
        "source_manifest": live.get("source_manifest") or {},
    }
    snapshot["snapshot_hash"] = value_hash(snapshot)
    call_snapshots = dict(live.get("model_call_snapshots") or {})
    existing = call_snapshots.get(logical_stage)
    if existing:
        if existing != snapshot and not (
            reuse_existing_input and _same_source_binding(existing, snapshot)
        ):
            raise ValueError(f"{logical_stage} 调用输入已冻结且发生变化")
        service.db.rollback()
        entry["model_call_snapshots"] = call_snapshots
        replay = (
            _replay_model_result(service.db, revision.business_id, logical_stage)
            if reuse_existing_input
            else None
        )
        resume = {"_reuse_existing_input": True} if reuse_existing_input else {}
        return {
            **existing,
            **resume,
            **({"_replay_text": replay} if replay else {}),
        }
    call_snapshots[logical_stage] = snapshot
    live["model_call_snapshots"] = call_snapshots
    chapters[str(position)] = live
    ledger["chapters"] = chapters
    locked.continuity_ledger = ledger
    service.db.commit()
    entry["model_call_snapshots"] = call_snapshots
    return snapshot


def frozen_prompt_and_replay(before_call, stage: str, prompt: str):
    if before_call is None:
        return prompt, None
    frozen = before_call(stage, prompt) or {}
    reuse = frozen.get("_reuse_existing_input")
    exact = frozen.get("input_hash") == value_hash(str(prompt))
    selected = frozen.get("normalized_input") if reuse and not exact else prompt
    return selected or prompt, frozen.get("_replay_text")


def _same_source_binding(existing: dict, current: dict) -> bool:
    ignored = {"normalized_input", "input_hash", "snapshot_hash"}
    return valid_call_snapshot(existing) and all(
        existing.get(key) == value
        for key, value in current.items()
        if key not in ignored
    )


def _replay_model_result(db, revision_business_id: str, logical_stage: str):
    scene = f"story_novel.{revision_business_id}.{logical_stage}"
    rows = LLMInvocationRepository(db).list_by_call_scene_prefix(scene)
    for row in reversed(rows):
        metadata = dict(row.response_metadata or {})
        if (
            row.call_scene == scene
            and row.status == "succeeded"
            and metadata.get("product_status", "accepted") == "accepted"
            and metadata.get("finish_reason") == "stop"
            and str(row.response or "").strip()
        ):
            return GeneratedNovelText(
                str(row.response).strip(), invocation_row_evidence(row)
            )
    return None


def valid_call_snapshot(snapshot: dict) -> bool:
    if not isinstance(snapshot, dict) or snapshot.get("schema") != SCHEMA:
        return False
    stored = snapshot.get("snapshot_hash")
    payload = {key: value for key, value in snapshot.items() if key != "snapshot_hash"}
    return bool(
        stored == value_hash(payload)
        and snapshot.get("input_hash")
        == value_hash(str(snapshot.get("normalized_input") or ""))
    )


def archive_failed_chapter_planning_calls(entry: dict, position: int) -> bool:
    """Archive response-derived repair inputs at a formal Resume boundary."""
    active = dict(entry.get("model_call_snapshots") or {})
    prefix = f"chapter_planning.{position}"
    failed = [key for key in active if key.startswith(f"{prefix}.")]
    if not failed:
        return False
    archived = list(entry.get("failed_model_call_snapshots") or [])
    for key in sorted(failed):
        archived.append(
            {
                "logical_stage": key,
                "reason": "formal_resume_after_failed_chapter_planning",
                "snapshot": active.pop(key),
            }
        )
    entry["model_call_snapshots"] = active
    entry["failed_model_call_snapshots"] = archived
    return True


def archive_regenerated_chapter_calls(entry: dict, position: int) -> bool:
    """Open one explicit prose attempt without weakening Resume replay."""
    active = dict(entry.get("model_call_snapshots") or {})
    prefixes = (
        f"prose.{position}",
        f"audit.{position}.",
        f"local_repair.{position}",
    )
    selected = [
        key for key in active if any(key.startswith(prefix) for prefix in prefixes)
    ]
    if not selected:
        return False
    archived = list(entry.get("regenerated_model_call_snapshots") or [])
    for key in sorted(selected):
        archived.append(
            {
                "logical_stage": key,
                "reason": "explicit_chapter_regeneration",
                "snapshot": active.pop(key),
            }
        )
    entry["model_call_snapshots"] = active
    entry["regenerated_model_call_snapshots"] = archived
    return True
