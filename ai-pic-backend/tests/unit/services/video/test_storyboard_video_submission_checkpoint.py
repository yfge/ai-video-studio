from __future__ import annotations

import pytest
from app.models.task import Task, TaskStatus, TaskType
from app.models.video_generation_task import (
    VideoGenerationTask,
    VideoGenerationTaskStatus,
)
from app.services.providers.base import AIModelType, AIResponse, AITaskType
from app.services.video.video_task_submission_service import VideoTaskSubmissionService
from tests.factories import ScriptFactory, UserFactory, setup_factories


def _context(db_session):
    setup_factories(db_session)
    user = UserFactory()
    script = ScriptFactory(
        extra_metadata={
            "storyboard": {
                "frames": [
                    {
                        "description": "Frame one",
                        "start_image_urls": ["https://example.com/one.png"],
                    },
                    {
                        "description": "Frame two",
                        "start_image_urls": ["https://example.com/two.png"],
                    },
                ]
            }
        }
    )
    task = Task(
        title="Storyboard video checkpoint",
        task_type=TaskType.VIDEO_GENERATION,
        prompt="Generate two clips",
        user_id=user.id,
    )
    db_session.add(task)
    db_session.commit()
    return script, task


def _success(task_id: str) -> AIResponse:
    return AIResponse(
        success=True,
        data={"task_id": task_id, "duration": 5},
        provider="volcengine",
        model="doubao-seedance-2-0-260128",
        task_type=AITaskType.VIDEO_GENERATION,
        model_type=AIModelType.IMAGE_TO_VIDEO,
    )


def test_provider_exception_becomes_durable_failed_child(
    db_session,
    monkeypatch,
) -> None:
    script, task = _context(db_session)
    responses = iter([_success("provider-one"), RuntimeError("transport crashed")])

    def fake_submit(*_args, **_kwargs):
        result = next(responses)
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(
        "app.services.video.video_task_submission_service.submit_provider_task",
        fake_submit,
    )

    VideoTaskSubmissionService(db_session, object()).submit_storyboard_video_tasks(
        task_id=task.id,
        script_id=script.id,
        frame_indexes=[0, 1],
        selections=None,
        options=None,
    )

    children = (
        db_session.query(VideoGenerationTask)
        .filter(VideoGenerationTask.task_id == task.id)
        .order_by(VideoGenerationTask.frame_index.asc())
        .all()
    )
    assert [child.status for child in children] == [
        VideoGenerationTaskStatus.SUBMITTED,
        VideoGenerationTaskStatus.FAILED,
    ]
    assert "transport crashed" in children[1].error_message
    assert task.status == TaskStatus.PROCESSING
    assert "transport crashed" in task.error_message


def test_first_provider_task_id_survives_later_database_failure(
    db_session,
    monkeypatch,
) -> None:
    script, task = _context(db_session)
    responses = iter(
        [
            _success("provider-one"),
            AIResponse(
                success=False,
                error="provider rejected frame two",
                provider="volcengine",
                model="doubao-seedance-2-0-260128",
                task_type=AITaskType.VIDEO_GENERATION,
                model_type=AIModelType.IMAGE_TO_VIDEO,
            ),
        ]
    )
    service = VideoTaskSubmissionService(db_session, object())
    monkeypatch.setattr(
        "app.services.video.video_task_submission_service.submit_provider_task",
        lambda *_args, **_kwargs: next(responses),
    )
    monkeypatch.setattr(
        service,
        "_record_failure",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            RuntimeError("failure persistence crashed")
        ),
    )

    with pytest.raises(RuntimeError, match="failure persistence crashed"):
        service.submit_storyboard_video_tasks(
            task_id=task.id,
            script_id=script.id,
            frame_indexes=[0, 1],
            selections=None,
            options=None,
        )
    db_session.rollback()

    children = (
        db_session.query(VideoGenerationTask)
        .filter(VideoGenerationTask.task_id == task.id)
        .all()
    )
    assert len(children) == 1
    assert children[0].frame_index == 0
    assert children[0].provider_task_id == "provider-one"


def test_parent_retry_submits_only_missing_frame_children(
    db_session,
    monkeypatch,
) -> None:
    script, task = _context(db_session)
    existing = VideoGenerationTask(
        task_id=task.id,
        script_id=script.id,
        frame_index=0,
        user_id=task.user_id,
        provider="volcengine",
        provider_task_id="provider-one",
        model="doubao-seedance-2-0-260128",
        model_type="image_to_video",
        status=VideoGenerationTaskStatus.SUBMITTED,
    )
    db_session.add(existing)
    db_session.commit()
    submitted_start_urls: list[str] = []

    def fake_submit(*_args, **kwargs):
        submitted_start_urls.append(kwargs["start_url"])
        return _success("provider-two")

    monkeypatch.setattr(
        "app.services.video.video_task_submission_service.submit_provider_task",
        fake_submit,
    )

    VideoTaskSubmissionService(db_session, object()).submit_storyboard_video_tasks(
        task_id=task.id,
        script_id=script.id,
        frame_indexes=[0, 1],
        selections=None,
        options=None,
    )

    children = (
        db_session.query(VideoGenerationTask)
        .filter(VideoGenerationTask.task_id == task.id)
        .order_by(VideoGenerationTask.frame_index.asc())
        .all()
    )
    assert submitted_start_urls == ["https://example.com/two.png"]
    assert [(child.frame_index, child.provider_task_id) for child in children] == [
        (0, "provider-one"),
        (1, "provider-two"),
    ]
