import json

from app.api.v1.endpoints.tasks import _dispatch_celery_task
from app.models.task import Task, TaskType


def test_dispatch_video_generation_routes_timeline_rework(monkeypatch):
    calls = []

    monkeypatch.setattr(
        "app.services.task_worker_storyboard_media.storyboard_video_generate_task.delay",
        lambda *args: calls.append(("storyboard", args)),
    )
    monkeypatch.setattr(
        "app.services.task_worker_timeline_rework.timeline_clip_rework_video_generate_task.delay",
        lambda *args: calls.append(("timeline_rework", args)),
    )
    params = {
        "timeline_id": 7,
        "timeline_version": 2,
        "clip_id": "video_scene_1_beat_2_001",
        "prompt": "regenerate this clip",
    }
    task = Task(
        id=123,
        title="Timeline clip rework",
        task_type=TaskType.VIDEO_GENERATION,
        parameters=json.dumps(params),
        user_id=9,
    )

    assert _dispatch_celery_task(task, user_id=9) is True

    assert calls == [("timeline_rework", (123, params, 9))]


def test_dispatch_timeline_generation_routes_audio_timeline(monkeypatch):
    calls = []

    monkeypatch.setattr(
        "app.services.task_worker.script_audio_timeline_generate_task.delay",
        lambda *args: calls.append(("audio_timeline", args)),
    )
    params = {"script_id": 42, "overwrite": True}
    task = Task(
        id=124,
        title="Audio timeline",
        task_type=TaskType.TIMELINE_GENERATION,
        parameters=json.dumps(params),
        user_id=9,
    )

    assert _dispatch_celery_task(task, user_id=9) is True

    assert calls == [("audio_timeline", (124, params, 9))]


def test_dispatch_timeline_clip_storyboard_routes_grid_worker(monkeypatch):
    calls = []

    monkeypatch.setattr(
        "app.services.task_worker_grid_storyboard.grid_storyboard_sheet_generate_task.delay",
        lambda *args: calls.append(("grid_storyboard", args)),
    )
    monkeypatch.setattr(
        "app.services.task_worker_storyboard_media.storyboard_image_generate_task.delay",
        lambda *args: calls.append(("legacy_storyboard", args)),
    )
    params = {
        "kind": "timeline_clip_storyboard",
        "timeline_id": 76,
        "clip_id": "video_scene_591_beat_4352_001",
    }
    task = Task(
        id=6449,
        title="Timeline clip storyboard",
        task_type=TaskType.STORYBOARD_IMAGE_GENERATION,
        parameters=json.dumps(params),
        user_id=9,
    )

    assert _dispatch_celery_task(task, user_id=9) is True

    assert calls == [("grid_storyboard", (6449, params, 9))]
