"""Persist and validate thread schedule checkpoints between planning retries."""

from __future__ import annotations

from .story_novel_canon_service import canonical_json, content_hash
from .story_novel_thread_schedule import parse_thread_payoffs, thread_schedule_contract


def reusable_thread_payoffs(frozen_spec: dict | None) -> list[dict] | None:
    if not frozen_spec or not isinstance(frozen_spec.get("thread_payoffs"), list):
        return None
    rows = frozen_spec["thread_payoffs"]
    if frozen_spec.get("thread_payoffs_hash") != content_hash(rows) or frozen_spec.get(
        "thread_payoffs_outline_hash"
    ) != frozen_spec.get("outline_hash"):
        return None
    contract = thread_schedule_contract(frozen_spec)
    parsed, error = parse_thread_payoffs(
        canonical_json({"thread_payoffs": rows}), contract or []
    )
    return None if error else parsed


def checkpoint_thread_payoffs(
    service, revision, task, frozen_spec: dict, rows: list[dict]
) -> None:
    checkpoint = {
        "thread_payoffs": rows,
        "thread_payoffs_hash": content_hash(rows),
        "thread_payoffs_outline_hash": frozen_spec.get("outline_hash"),
    }
    frozen_spec.update(checkpoint)
    revision.generation_plan = {
        **dict(revision.generation_plan or {}),
        **checkpoint,
    }
    task.description = "伏笔调度完成，正在规划章节合同…"
    service.db.commit()
