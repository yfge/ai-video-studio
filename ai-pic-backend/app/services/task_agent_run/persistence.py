"""
Persist agent execution traces into Task.parameters.agent_run.

We already store provider/model/usage metadata on target entities (Story/Episode/Script)
via extra_metadata.agent_run. This package copies the essential audit trail into the Task
record so operators can inspect executions directly from /tasks UI.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from app.services.task_agent_run.builder import build_agent_run
from app.services.task_agent_run.utils import deep_merge_dict, loads_task_parameters


def persist_task_agent_run(
    *,
    task_id: int,
    user_id: int,
    kind: str,
    request_dict: Optional[Dict[str, Any]] = None,
    db_session=None,
) -> None:
    """Persist agent_run into Task.parameters for a terminal task (completed/failed/cancelled)."""

    from app.models.task import Task, TaskStatus

    should_close = False
    if db_session is None:
        from app.core.database import SessionLocal

        db = SessionLocal()
        should_close = True
    else:
        db = db_session
    try:
        task: Task | None = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return
        terminal_statuses = {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED}
        if task.status not in terminal_statuses:
            return

        agent_run = build_agent_run(
            db, task, user_id=user_id, kind=kind, request_dict=request_dict
        )
        if not agent_run and task.status == TaskStatus.COMPLETED:
            return

        if task.status in {TaskStatus.FAILED, TaskStatus.CANCELLED}:
            agent_run = _enrich_with_failure_context(task, kind=kind, agent_run=agent_run)

        if not agent_run:
            return

        _patch_task_parameters(db, task, {"agent_run": agent_run})
    finally:
        if should_close:
            db.close()


def _enrich_with_failure_context(task, *, kind: str, agent_run: Dict[str, Any]) -> Dict[str, Any]:
    enriched: Dict[str, Any] = dict(agent_run or {})
    if not enriched.get("generation_method") and kind:
        enriched["generation_method"] = kind
    if not enriched.get("prompt") and getattr(task, "prompt", None):
        enriched["prompt"] = task.prompt
    enriched["task_status"] = getattr(task.status, "value", str(task.status))

    error_message = getattr(task, "error_message", None)
    if isinstance(error_message, str) and error_message.strip():
        enriched["error"] = {"message": error_message.strip()}

    if not enriched.get("result_ref"):
        result_ref = _best_effort_result_ref(task)
        if result_ref:
            enriched["result_ref"] = result_ref

    return enriched


def _best_effort_result_ref(task) -> Dict[str, Any]:
    params = loads_task_parameters(getattr(task, "parameters", None))
    keys = (
        "story_id",
        "episode_id",
        "script_id",
        "virtual_ip_id",
        "env_id",
        "environment_id",
    )
    return {key: params[key] for key in keys if key in params}


def _patch_task_parameters(db, task, patch: Dict[str, Any]) -> None:
    base = loads_task_parameters(task.parameters)
    merged = deep_merge_dict(base, patch)
    task.parameters = json.dumps(merged, ensure_ascii=False)
    db.commit()
