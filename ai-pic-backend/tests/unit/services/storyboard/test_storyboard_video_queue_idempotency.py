from __future__ import annotations

import copy
import json

import pytest
from app.models.task import Task, TaskStatus, TaskType
from app.models.timeline import Timeline
from app.services.storyboard.video_generation_queue import (
    queue_storyboard_video_generation_task,
)
from tests.factories import ScriptFactory, UserFactory, setup_factories


def _queue_context(db_session):
    setup_factories(db_session)
    user = UserFactory()
    script = ScriptFactory(extra_metadata={})
    timeline = Timeline(
        episode_id=script.episode_id,
        script_id=script.id,
        title="Idempotency timeline",
        status="draft",
        version=2,
        spec={
            "tracks": [
                {
                    "track_type": "video",
                    "clips": [
                        {"clip_id": "stable-clip-1"},
                        {"clip_id": "stable-clip-2"},
                    ],
                }
            ]
        },
        created_by=user.id,
    )
    db_session.add(timeline)
    db_session.commit()
    script.extra_metadata = {
        "storyboard": {
            "frames": [
                {
                    "frame_id": "frame-1",
                    "description": "Opening shot",
                    "start_image_urls": ["https://example.com/frame-1.png"],
                    "source": {
                        "timeline_id": timeline.id,
                        "timeline_version": 1,
                        "clip_id": "stable-clip-1",
                    },
                },
                {
                    "frame_id": "frame-2",
                    "description": "Changed shot",
                    "start_image_urls": ["https://example.com/frame-2.png"],
                    "source": {
                        "timeline_id": timeline.id,
                        "timeline_version": 2,
                        "clip_id": "stable-clip-2",
                    },
                },
            ]
        }
    }
    db_session.commit()
    return user, script


def _queue(db_session, user, script, **overrides):
    options = {
        "frame_indexes": [0],
        "model": "volcengine:seedance-2",
        "target_business_id": "canvas-run-a",
    }
    options.update(overrides)
    return queue_storyboard_video_generation_task(
        db_session,
        user,
        script,
        **options,
    )


def test_identical_active_storyboard_video_request_reuses_task(
    db_session,
    monkeypatch,
) -> None:
    user, script = _queue_context(db_session)
    dispatched: list[int] = []
    monkeypatch.setattr(
        "app.services.storyboard.video_generation_queue."
        "storyboard_video_generate_task.delay",
        lambda task_id, _payload, _user_id: dispatched.append(task_id),
    )

    first = _queue(db_session, user, script)
    second = _queue(db_session, user, script)

    assert second.reused is True
    assert second.task.id == first.task.id
    assert dispatched == [first.task.id]
    tasks = (
        db_session.query(Task).filter(Task.task_type == TaskType.VIDEO_GENERATION).all()
    )
    assert len(tasks) == 1
    assert json.loads(tasks[0].parameters)["request_fingerprint"]


def test_storyboard_video_output_checkpoint_does_not_change_active_request(
    db_session,
    monkeypatch,
) -> None:
    user, script = _queue_context(db_session)
    dispatched: list[int] = []
    monkeypatch.setattr(
        "app.services.storyboard.video_generation_queue."
        "storyboard_video_generate_task.delay",
        lambda task_id, _payload, _user_id: dispatched.append(task_id),
    )
    first = _queue(db_session, user, script)
    metadata = copy.deepcopy(script.extra_metadata)
    frame = metadata["storyboard"]["frames"][0]
    frame["video_url"] = "https://example.com/generated-video.mp4"
    frame["video_urls"] = [frame["video_url"]]
    frame["video_generation"] = {"provider": "volcengine"}
    script.extra_metadata = metadata
    db_session.commit()

    repeated = _queue(db_session, user, script)

    assert repeated.reused is True
    assert repeated.task.id == first.task.id
    assert dispatched == [first.task.id]


@pytest.mark.parametrize(
    "overrides",
    [
        {"model": "volcengine:changed-model"},
        {"frame_indexes": [1]},
        {"target_business_id": "canvas-run-b"},
    ],
)
def test_storyboard_video_worker_input_change_creates_new_task(
    db_session,
    monkeypatch,
    overrides,
) -> None:
    user, script = _queue_context(db_session)
    dispatched: list[int] = []
    monkeypatch.setattr(
        "app.services.storyboard.video_generation_queue."
        "storyboard_video_generate_task.delay",
        lambda task_id, _payload, _user_id: dispatched.append(task_id),
    )

    first = _queue(db_session, user, script)
    changed = _queue(db_session, user, script, **overrides)

    assert changed.reused is False
    assert changed.task.id != first.task.id
    assert dispatched == [first.task.id, changed.task.id]


@pytest.mark.parametrize(
    "terminal_status",
    [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED],
)
def test_terminal_storyboard_video_task_is_retryable(
    db_session,
    monkeypatch,
    terminal_status,
) -> None:
    user, script = _queue_context(db_session)
    dispatched: list[int] = []
    monkeypatch.setattr(
        "app.services.storyboard.video_generation_queue."
        "storyboard_video_generate_task.delay",
        lambda task_id, _payload, _user_id: dispatched.append(task_id),
    )
    first = _queue(db_session, user, script)
    first.task.status = terminal_status
    db_session.commit()

    retry = _queue(db_session, user, script)

    assert retry.reused is False
    assert retry.task.id != first.task.id
    assert dispatched == [first.task.id, retry.task.id]


def test_storyboard_video_dispatch_failure_marks_task_failed(
    db_session,
    monkeypatch,
) -> None:
    user, script = _queue_context(db_session)

    def fail_dispatch(*_args, **_kwargs):
        raise RuntimeError("celery transport unavailable")

    monkeypatch.setattr(
        "app.services.storyboard.video_generation_queue."
        "storyboard_video_generate_task.delay",
        fail_dispatch,
    )

    with pytest.raises(RuntimeError, match="celery transport unavailable"):
        _queue(db_session, user, script)

    task = (
        db_session.query(Task)
        .filter(Task.task_type == TaskType.VIDEO_GENERATION)
        .order_by(Task.id.desc())
        .first()
    )
    assert task.status == TaskStatus.FAILED
    assert "celery transport unavailable" in task.error_message
