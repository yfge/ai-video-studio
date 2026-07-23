"""Celery-side orchestration for explicit memory extraction."""

import anyio
from app.core.database import get_task_db
from app.models.task import TaskStatus
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.schemas.narrative_extraction import NarrativeExtractionRequest
from app.services.narrative_memory.access import require_story
from app.services.narrative_memory.extraction_service import NarrativeExtractionService


def process_narrative_memory_extraction(
    task_id: int, story_business_id: str, payload: dict, user_id: int
) -> None:
    with get_task_db() as db:
        tasks = TaskRepository(db)
        task = tasks.get_by_id(task_id)
        if not task:
            return
        try:
            task.status = TaskStatus.PROCESSING
            db.commit()
            repo = NarrativeMemoryRepository(db)
            user = UserRepository(db).get_by_id(user_id)
            story = require_story(repo, story_business_id, user)

            async def _run():
                return await NarrativeExtractionService(repo).extract(
                    story, NarrativeExtractionRequest(**payload), user
                )

            result = anyio.run(_run)
            task.status = TaskStatus.COMPLETED
            task.result_file_path = (
                f"narrative-memory:{story_business_id}:"
                f"{len(result['events'])}:{len(result['memories'])}"
            )
            db.commit()
        except Exception as exc:
            db.rollback()
            task = tasks.get_by_id(task_id)
            if task:
                task.status = TaskStatus.FAILED
                task.error_message = str(exc) or repr(exc)
                db.commit()
