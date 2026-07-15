from __future__ import annotations

import json

import pytest
from app.models.task import Task, TaskStatus, TaskType
from app.services.storyboard.storyboard_image_autogen import (
    StoryboardImageQueueResult,
    queue_storyboard_image_generation,
    storyboard_image_queue_progress_message,
)
from tests.factories import ScriptFactory, UserFactory, setup_factories


def _script_with_frame():
    return ScriptFactory(
        extra_metadata={
            "storyboard": {
                "frames": [
                    {
                        "frame_id": "frame-1",
                        "description": "Environment insert",
                        "characters": [],
                    }
                ]
            }
        }
    )


def test_identical_active_storyboard_image_request_reuses_task(
    db_session,
    monkeypatch,
) -> None:
    setup_factories(db_session)
    user = UserFactory()
    script = _script_with_frame()
    db_session.commit()
    dispatched: list[int] = []
    monkeypatch.setattr(
        "app.services.storyboard.storyboard_image_autogen."
        "storyboard_image_generate_task.delay",
        lambda task_id, _payload, _user_id: dispatched.append(task_id),
    )

    first = queue_storyboard_image_generation(
        db_session,
        script_id=script.id,
        user_id=user.id,
        require_reference_images=True,
    )
    second = queue_storyboard_image_generation(
        db_session,
        script_id=script.id,
        user_id=user.id,
        require_reference_images=True,
    )

    assert second.status == "reused"
    assert second.reason == "existing_active_task"
    assert second.child_task_id == first.child_task_id
    assert dispatched == [first.child_task_id]
    tasks = (
        db_session.query(Task)
        .filter(Task.task_type == TaskType.STORYBOARD_IMAGE_GENERATION)
        .all()
    )
    assert len(tasks) == 1
    assert json.loads(tasks[0].parameters)["request_fingerprint"]


def test_storyboard_image_request_scope_changes_fingerprint(
    db_session,
    monkeypatch,
) -> None:
    setup_factories(db_session)
    user = UserFactory()
    script = _script_with_frame()
    db_session.commit()
    dispatched: list[int] = []
    monkeypatch.setattr(
        "app.services.storyboard.storyboard_image_autogen."
        "storyboard_image_generate_task.delay",
        lambda task_id, _payload, _user_id: dispatched.append(task_id),
    )

    first = queue_storyboard_image_generation(
        db_session,
        script_id=script.id,
        user_id=user.id,
        idempotency_scope="canvas-run-a",
    )
    second = queue_storyboard_image_generation(
        db_session,
        script_id=script.id,
        user_id=user.id,
        idempotency_scope="canvas-run-b",
    )

    assert first.child_task_id != second.child_task_id
    assert dispatched == [first.child_task_id, second.child_task_id]


def test_storyboard_image_worker_input_changes_create_new_tasks(
    db_session,
    monkeypatch,
) -> None:
    setup_factories(db_session)
    user = UserFactory()
    script = _script_with_frame()
    db_session.commit()
    dispatched: list[int] = []
    monkeypatch.setattr(
        "app.services.storyboard.storyboard_image_autogen."
        "storyboard_image_generate_task.delay",
        lambda task_id, _payload, _user_id: dispatched.append(task_id),
    )

    results = [
        queue_storyboard_image_generation(
            db_session,
            script_id=script.id,
            user_id=user.id,
        ),
        queue_storyboard_image_generation(
            db_session,
            script_id=script.id,
            user_id=user.id,
            model="openai:changed-model",
        ),
        queue_storyboard_image_generation(
            db_session,
            script_id=script.id,
            user_id=user.id,
            prompt="Changed prompt",
        ),
        queue_storyboard_image_generation(
            db_session,
            script_id=script.id,
            user_id=user.id,
            reference_images=["https://example.com/changed-reference.png"],
        ),
        queue_storyboard_image_generation(
            db_session,
            script_id=script.id,
            user_id=user.id,
            frames=[
                {
                    "frame_id": "frame-1",
                    "description": "Changed frame snapshot",
                    "characters": [],
                }
            ],
        ),
    ]

    task_ids = [result.child_task_id for result in results]
    assert len(set(task_ids)) == len(task_ids)
    assert dispatched == task_ids


@pytest.mark.parametrize(
    "terminal_status",
    [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED],
)
def test_terminal_storyboard_image_task_is_retryable(
    db_session,
    monkeypatch,
    terminal_status,
) -> None:
    setup_factories(db_session)
    user = UserFactory()
    script = _script_with_frame()
    db_session.commit()
    dispatched: list[int] = []
    monkeypatch.setattr(
        "app.services.storyboard.storyboard_image_autogen."
        "storyboard_image_generate_task.delay",
        lambda task_id, _payload, _user_id: dispatched.append(task_id),
    )
    first = queue_storyboard_image_generation(
        db_session,
        script_id=script.id,
        user_id=user.id,
    )
    task = db_session.get(Task, first.child_task_id)
    task.status = terminal_status
    db_session.commit()

    retry = queue_storyboard_image_generation(
        db_session,
        script_id=script.id,
        user_id=user.id,
    )

    assert retry.status == "queued"
    assert retry.child_task_id != first.child_task_id
    assert dispatched == [first.child_task_id, retry.child_task_id]


def test_storyboard_image_dispatch_failure_marks_task_failed(
    db_session,
    monkeypatch,
) -> None:
    setup_factories(db_session)
    user = UserFactory()
    script = _script_with_frame()
    db_session.commit()

    def fail_dispatch(*_args, **_kwargs):
        raise RuntimeError("celery transport unavailable")

    monkeypatch.setattr(
        "app.services.storyboard.storyboard_image_autogen."
        "storyboard_image_generate_task.delay",
        fail_dispatch,
    )

    with pytest.raises(RuntimeError, match="celery transport unavailable"):
        queue_storyboard_image_generation(
            db_session,
            script_id=script.id,
            user_id=user.id,
        )

    task = (
        db_session.query(Task)
        .filter(Task.task_type == TaskType.STORYBOARD_IMAGE_GENERATION)
        .order_by(Task.id.desc())
        .first()
    )
    assert task.status == TaskStatus.FAILED
    assert "celery transport unavailable" in task.error_message


def test_reused_storyboard_image_progress_message_is_explicit() -> None:
    result = StoryboardImageQueueResult(
        status="reused",
        child_task_id=123,
        queued_frame_indexes=[0],
        skipped_frame_indexes=[],
        require_reference_images=True,
        reason="existing_active_task",
    )

    message = storyboard_image_queue_progress_message(result, prefix="Storyboard")

    assert "已复用" in message
    assert "已创建" not in message
