from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any

from app.core.database import SessionLocal
from app.models.task import Task, TaskStatus
from app.repositories.script_repository import ScriptRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.script_quality import ScriptLintOptions
from app.services.ai_service import ai_service
from app.services.script_quality.lint_engine import lint_script_content_async


def _load_task_parameters(task: Task) -> dict[str, Any]:
    if not task.parameters:
        return {}
    try:
        parsed = json.loads(task.parameters)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _dump_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def process_script_quality_task(
    task_id: int, payload: dict[str, Any], user_id: int
) -> None:
    """
    Celery entrypoint: run script QC and persist results.

    - Updates Task.status/description/error_message
    - Persists result into Task.parameters.result and Script.extra_metadata.script_quality
    """
    db = SessionLocal()
    task: Task | None = None
    try:
        task = TaskRepository(db).get_by_id(task_id)
        if task is None:
            return
        task.status = TaskStatus.PROCESSING
        task.description = "剧本质检中…"
        db.commit()

        script_id = int(payload.get("script_id"))
        script = ScriptRepository(db).get_by_id(script_id)
        if script is not None and script.is_deleted:
            script = None
        if script is None:
            raise RuntimeError("script_not_found")

        options_dict = payload.get("options") or {}
        options = (
            ScriptLintOptions(**options_dict)
            if isinstance(options_dict, dict)
            else ScriptLintOptions()
        )
        result = asyncio.run(
            lint_script_content_async(
                script.content or "",
                options=options,
                ai_manager=getattr(ai_service, "ai_manager", None),
            )
        )
        result_payload = result.model_dump(mode="json")

        # Persist on script.extra_metadata (SQLAlchemy JSON needs reassignment; in-place mutation won't persist)
        meta = script.extra_metadata if isinstance(script.extra_metadata, dict) else {}
        script.extra_metadata = {
            **meta,
            "script_quality": {
                "result": result_payload,
                "updated_at": datetime.utcnow().isoformat(),
                "task_id": task_id,
                "user_id": user_id,
            },
        }

        # Persist on task.parameters
        params = _load_task_parameters(task)
        params.update(payload)
        params["result"] = result_payload
        task.parameters = _dump_json(params)
        task.status = TaskStatus.COMPLETED
        task.description = "剧本质检完成"
        task.result_file_path = f"script:{script_id}:quality"
        db.commit()
    except Exception as exc:
        if task is not None:
            task.status = TaskStatus.FAILED
            task.error_message = str(exc)
            task.description = f"剧本质检失败：{exc}"
            db.commit()
    finally:
        db.close()
