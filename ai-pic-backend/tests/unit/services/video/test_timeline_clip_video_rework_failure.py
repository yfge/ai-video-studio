import json

import pytest
from app.models.task import Task, TaskStatus, TaskType
from app.models.user import User
from app.models.video_generation_task import (
    VideoGenerationTask,
    VideoGenerationTaskStatus,
)
from app.services.providers.base import AIModelType, AIResponse, AITaskType
from app.services.timeline_clip_video_rework_submission import (
    TimelineClipVideoReworkSubmissionService,
)


def test_timeline_video_failure_preserves_provider_model_and_external_blocker(
    db_session, monkeypatch
):
    user = User(
        username="timeline_failure_worker",
        email="timeline_failure_worker@example.com",
        hashed_password="test",
        is_active=True,
        is_approved=True,
        email_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    task = Task(
        target_business_id="timeline-failure",
        title="Timeline video failure",
        task_type=TaskType.VIDEO_GENERATION,
        prompt="Animate the whole storyboard sheet",
        user_id=user.id,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    request_id = "021784105426127e7a0e121a78287261e362ecd929ed85342f035"

    def fake_submit_provider_task(*_args, **_kwargs):
        return AIResponse(
            success=False,
            error=(
                "403 Forbidden: AccountOverdueError, overdue balance. "
                f"Request id: {request_id}"
            ),
            provider="volcengine",
            model="doubao-seedance-2-0-260128",
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=AIModelType.IMAGE_TO_VIDEO,
        )

    monkeypatch.setattr(
        "app.services.timeline_clip_video_rework_submission.submit_provider_task",
        fake_submit_provider_task,
    )
    payload = {
        "timeline_id": 69,
        "timeline_business_id": "tl_69",
        "timeline_version": 10,
        "clip_id": "video_scene_91_beat_4001_011",
        "action": "re_cut",
        "prompt": "Animate the whole storyboard sheet",
        "reference_images": ["https://example.com/storyboard.png"],
        "duration": 6.26,
        "model": "volcengine:doubao-seedance-2-0-260128",
        "fps": 24,
        "resolution": "720p",
        "ratio": "9:16",
        "reference_mode": "clip_storyboard_sheet",
        "clip_storyboard": {"mode": "sheet_sequence", "panel_count": 4},
    }

    with pytest.raises(RuntimeError, match="AccountOverdueError"):
        TimelineClipVideoReworkSubmissionService(db_session, object()).submit(
            task_id=task.id,
            payload=payload,
            user_id=user.id,
        )

    db_session.refresh(task)
    child = (
        db_session.query(VideoGenerationTask)
        .filter(VideoGenerationTask.task_id == task.id)
        .one()
    )
    params = json.loads(child.parameters)
    assert task.status == TaskStatus.FAILED
    assert child.status == VideoGenerationTaskStatus.FAILED
    assert child.provider == "volcengine"
    assert child.model == "doubao-seedance-2-0-260128"
    assert child.model_type == "image_to_video"
    assert params["target_duration_seconds"] == 6.26
    assert params["provider_duration_seconds"] == 7
    assert params["timeline_rework"]["clip_id"] == payload["clip_id"]
    assert params["timeline_rework"]["reference_mode"] == "clip_storyboard_sheet"
    assert params["submission_failure"] == {
        "category": "external_dependency_unavailable",
        "code": "account_overdue",
        "retryable": False,
        "provider_request_id": request_id,
    }
    assert (
        child.generation_metadata["submission_failure"] == params["submission_failure"]
    )


def test_storyboard_privacy_rejection_preserves_grid_failure_without_fallback(
    db_session, monkeypatch
):
    user = User(
        username="timeline_privacy_grid_worker",
        email="timeline_privacy_grid_worker@example.com",
        hashed_password="test",
        is_active=True,
        is_approved=True,
        email_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    task = Task(
        target_business_id="timeline-privacy-grid",
        title="Timeline privacy grid rejection",
        task_type=TaskType.VIDEO_GENERATION,
        prompt="Animate the whole storyboard sheet",
        user_id=user.id,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    request_id = "021784106049088f952b6c252d6ae62c15909f77d85597eae4b37"
    calls = []

    def fake_submit_provider_task(*_args, **kwargs):
        calls.append(kwargs)
        return AIResponse(
            success=False,
            error=(
                "InputImageSensitiveContentDetected.PrivacyInformation: "
                "The input image may contain real person. "
                f"Request id: {request_id}"
            ),
            provider="volcengine",
            model="doubao-seedance-2-0-260128",
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=AIModelType.IMAGE_TO_VIDEO,
        )

    monkeypatch.setattr(
        "app.services.timeline_clip_video_rework_submission.submit_provider_task",
        fake_submit_provider_task,
    )
    payload = {
        "timeline_id": 69,
        "timeline_business_id": "tl_69",
        "timeline_version": 10,
        "clip_id": "video_scene_91_beat_4001_011",
        "action": "re_cut",
        "prompt": "Animate the whole storyboard sheet",
        "reference_images": ["https://example.com/storyboard.png"],
        "duration": 6.26,
        "model": "volcengine:doubao-seedance-2-0-260128",
        "fps": 24,
        "resolution": "720p",
        "ratio": "9:16",
        "reference_mode": "clip_storyboard_sheet",
        "clip_storyboard": {"mode": "sheet_sequence", "panel_count": 4},
        "bound_context": {
            "characters": [
                {"name": "阿盖儿", "appearance_brief": "十六七岁的虚构少女"}
            ],
            "environment": {"hint": "公寓厨房"},
        },
    }

    with pytest.raises(RuntimeError, match="PrivacyInformation"):
        TimelineClipVideoReworkSubmissionService(db_session, object()).submit(
            task_id=task.id,
            payload=payload,
            user_id=user.id,
        )

    db_session.refresh(task)
    child = (
        db_session.query(VideoGenerationTask)
        .filter(VideoGenerationTask.task_id == task.id)
        .one()
    )
    params = json.loads(child.parameters)
    assert len(calls) == 1
    assert calls[0]["reference_images"] == payload["reference_images"]
    assert task.status == TaskStatus.FAILED
    assert child.status == VideoGenerationTaskStatus.FAILED
    assert child.model_type == "image_to_video"
    assert params["reference_images"] == payload["reference_images"]
    assert params["timeline_rework"]["reference_mode"] == "clip_storyboard_sheet"
    assert "visual_reference_fallback" not in params["timeline_rework"]
    assert params["submission_failure"] == {
        "category": "input_rejected",
        "code": "reference_privacy_rejected",
        "retryable": False,
        "provider_request_id": request_id,
    }
    assert (
        child.generation_metadata["submission_failure"] == params["submission_failure"]
    )
