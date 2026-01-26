"""
Celery task registrations for script quality checks.

Kept in a dedicated module to avoid growing app.services.task_worker further.
"""

from __future__ import annotations

from typing import Any, Dict

from app.core.celery_app import celery_app


@celery_app.task(name="tasks.script_quality_check")
def script_quality_check_task(task_id: int, payload: Dict[str, Any], user_id: int) -> None:
    """Run deterministic script QC and persist results."""
    from app.services.script_quality.task_entrypoints import process_script_quality_task

    process_script_quality_task(task_id, payload, user_id)

