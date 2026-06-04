import json

from app.models.task import Task, TaskType
from app.models.user import User
from app.models.video_generation_task import VideoGenerationTask
from app.services.providers.base import AIModelType, AIResponse, AITaskType
from app.services.timeline_clip_video_rework_submission import (
    TimelineClipVideoReworkSubmissionService,
)


def test_grid_rework_submission_records_reference_only_request_as_i2v(
    db_session, monkeypatch
):
    user = _user(db_session)
    task = Task(
        target_business_id="timeline-test",
        title="Grid rework",
        task_type=TaskType.VIDEO_GENERATION,
        prompt="Use panel 4 only",
        user_id=user.id,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    captured = {}

    def fake_submit_provider_task(
        _dispatcher,
        *,
        prompt,
        start_url,
        end_url,
        reference_images,
        duration,
        opts,
    ):
        captured.update(
            start_url=start_url,
            end_url=end_url,
            reference_images=reference_images,
        )
        return AIResponse(
            success=True,
            data={"task_id": "provider-task-grid", "duration": duration},
            provider="volcengine",
            model="doubao-seedance-2-0-260128",
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=AIModelType.IMAGE_TO_VIDEO,
        )

    monkeypatch.setattr(
        "app.services.timeline_clip_video_rework_submission.submit_provider_task",
        fake_submit_provider_task,
    )
    payload = _grid_payload()

    TimelineClipVideoReworkSubmissionService(db_session, object()).submit(
        task_id=task.id,
        payload=payload,
        user_id=user.id,
    )

    video_task = (
        db_session.query(VideoGenerationTask)
        .filter(VideoGenerationTask.task_id == task.id)
        .one()
    )
    params = json.loads(video_task.parameters)
    assert captured["start_url"] is None
    assert captured["reference_images"] == ["https://example.com/storyboard-grid.png"]
    assert video_task.model_type == "image_to_video"
    assert video_task.generation_metadata["model_type"] == "image_to_video"
    assert params["reference_images"] == ["https://example.com/storyboard-grid.png"]
    assert params["timeline_rework"]["reference_mode"] == "storyboard_grid_panel"


def test_clip_storyboard_rework_submission_records_reference_only_request_as_i2v(
    db_session, monkeypatch
):
    user = _user(db_session)
    task = Task(
        target_business_id="timeline-test",
        title="Clip storyboard rework",
        task_type=TaskType.VIDEO_GENERATION,
        prompt="Use panel 2 only",
        user_id=user.id,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    captured = {}

    def fake_submit_provider_task(
        _dispatcher,
        *,
        prompt,
        start_url,
        end_url,
        reference_images,
        duration,
        opts,
    ):
        captured.update(
            start_url=start_url,
            end_url=end_url,
            reference_images=reference_images,
        )
        return AIResponse(
            success=True,
            data={"task_id": "provider-task-clip-storyboard", "duration": duration},
            provider="volcengine",
            model="doubao-seedance-2-0-260128",
            task_type=AITaskType.VIDEO_GENERATION,
            model_type=AIModelType.IMAGE_TO_VIDEO,
        )

    monkeypatch.setattr(
        "app.services.timeline_clip_video_rework_submission.submit_provider_task",
        fake_submit_provider_task,
    )
    payload = _clip_storyboard_payload()

    TimelineClipVideoReworkSubmissionService(db_session, object()).submit(
        task_id=task.id,
        payload=payload,
        user_id=user.id,
    )

    video_task = (
        db_session.query(VideoGenerationTask)
        .filter(VideoGenerationTask.task_id == task.id)
        .one()
    )
    params = json.loads(video_task.parameters)
    assert captured["start_url"] is None
    assert captured["reference_images"] == [
        "https://example.com/clip-storyboard.png"
    ]
    assert video_task.model_type == "image_to_video"
    assert video_task.generation_metadata["model_type"] == "image_to_video"
    assert params["reference_images"] == ["https://example.com/clip-storyboard.png"]
    assert params["timeline_rework"]["reference_mode"] == "clip_storyboard_panel"
    assert params["timeline_rework"]["clip_storyboard"]["panel_index"] == 2


def _user(db_session):
    user = User(
        username="grid_worker",
        email="grid_worker@example.com",
        hashed_password="test",
        is_active=True,
        is_approved=True,
        email_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _grid_payload() -> dict:
    return {
        "timeline_id": 10,
        "timeline_business_id": "tl_10",
        "timeline_version": 2,
        "clip_id": "video_scene_001_beat_001_001",
        "action": "re_cut",
        "prompt": "Use panel 4 only",
        "image_url": None,
        "end_image_url": None,
        "reference_images": ["https://example.com/storyboard-grid.png"],
        "duration": 4,
        "model": "volcengine:doubao-seedance-2-0-260128",
        "fps": 24,
        "resolution": "720p",
        "reference_mode": "storyboard_grid_panel",
        "storyboard_grid": {"panel_id": "grid_panel_004", "panel_index": 4},
    }


def _clip_storyboard_payload() -> dict:
    return {
        "timeline_id": 10,
        "timeline_business_id": "tl_10",
        "timeline_version": 2,
        "clip_id": "video_scene_001_beat_001_001",
        "action": "re_cut",
        "prompt": "Use panel 2 only",
        "image_url": None,
        "end_image_url": None,
        "reference_images": ["https://example.com/clip-storyboard.png"],
        "duration": 4,
        "model": "volcengine:doubao-seedance-2-0-260128",
        "fps": 24,
        "resolution": "720p",
        "reference_mode": "clip_storyboard_panel",
        "clip_storyboard": {
            "panel_id": "clip_storyboard_panel_002",
            "panel_index": 2,
        },
    }
