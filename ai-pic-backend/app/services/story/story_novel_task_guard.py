"""Cooperative cancellation checks around durable novel-task writes."""

from app.models.task import TaskStatus
from app.repositories.task_repository import TaskRepository


class NovelTaskCancelled(Exception):
    pass


def ensure_task_not_cancelled(db, task) -> None:
    task_id = getattr(task, "id", None)
    if task_id is not None and hasattr(db, "get_bind"):
        status = TaskRepository(db).get_status_fresh(task_id)
    else:
        status = getattr(task, "status", None)
    if status in {TaskStatus.CANCELLED, "cancelled"}:
        raise NovelTaskCancelled()


async def generate_text_unless_cancelled(
    db,
    task,
    generate_text,
    revision,
    prompt: str,
    *,
    max_tokens: int | None,
    temperature: float | None = None,
    stage: str | None = None,
    model_override: str | None = None,
) -> str:
    """Check cancellation on both sides of every potentially long provider call."""
    ensure_task_not_cancelled(db, task)
    options = {"max_tokens": max_tokens}
    if temperature is not None:
        options["temperature"] = temperature
    if stage is not None:
        options["stage"] = stage
    if model_override is not None:
        options["model_override"] = model_override
    result = await generate_text(
        revision,
        prompt,
        **options,
    )
    ensure_task_not_cancelled(db, task)
    return result
