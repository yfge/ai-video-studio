"""Celery entrypoints for explicit narrative-memory provider operations."""

from typing import Any, Dict

from app.core.celery_app import celery_app


@celery_app.task(name="tasks.narrative_memory_extract")
def narrative_memory_extract_task(
    task_id: int, story_business_id: str, payload: Dict[str, Any], user_id: int
) -> None:
    from app.services.narrative_memory.extraction_task_processor import (
        process_narrative_memory_extraction,
    )

    process_narrative_memory_extraction(task_id, story_business_id, payload, user_id)


@celery_app.task(name="tasks.dramatic_state_suggest")
def dramatic_state_suggest_task(
    task_id: int,
    script_business_id: str,
    scene_business_id: str,
    payload: Dict[str, Any],
    user_id: int,
) -> None:
    from app.services.narrative_memory.dramatic_state_suggestion import (
        process_dramatic_state_suggestion,
    )

    process_dramatic_state_suggestion(
        task_id, script_business_id, scene_business_id, payload, user_id
    )
