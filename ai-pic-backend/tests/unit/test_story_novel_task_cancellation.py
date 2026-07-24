import anyio
import pytest
from app.models.task import Task, TaskStatus
from app.services.story.story_novel_task_guard import (
    NovelTaskCancelled,
    generate_text_unless_cancelled,
)
from sqlalchemy.orm import Session
from tests.unit.test_story_novel_longform import _setup


def test_provider_result_is_discarded_when_task_was_cancelled_mid_call():
    class Database:
        @staticmethod
        def refresh(_task):
            return None

    class Task:
        status = "pending"

    task = Task()
    calls = []

    async def provider(revision, prompt, *, max_tokens):
        calls.append((revision, prompt, max_tokens))
        task.status = "cancelled"
        return "must-not-be-used"

    async def run():
        return await generate_text_unless_cancelled(
            Database(),
            task,
            provider,
            object(),
            "prompt",
            max_tokens=9500,
        )

    with pytest.raises(NovelTaskCancelled):
        anyio.run(run)
    assert len(calls) == 1


def test_provider_guard_reads_cancel_from_separate_committed_transaction(db_session):
    _user, _story, _service, _revision, task, *_ = _setup(db_session)
    task.status = TaskStatus.PROCESSING
    db_session.commit()
    calls = []

    async def provider(_revision, _prompt, *, max_tokens):
        calls.append(max_tokens)
        with Session(bind=db_session.get_bind()) as external:
            row = external.query(Task).filter(Task.id == task.id).one()
            row.status = TaskStatus.CANCELLED
            external.commit()
        return "discard"

    async def run():
        return await generate_text_unless_cancelled(
            db_session,
            task,
            provider,
            object(),
            "prompt",
            max_tokens=9500,
        )

    with pytest.raises(NovelTaskCancelled):
        anyio.run(run)
    assert calls == [9500]
