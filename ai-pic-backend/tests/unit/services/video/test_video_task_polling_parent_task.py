import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.models.task import TaskStatus
from app.models.video_generation_task import VideoGenerationTaskStatus
from app.services.video import video_task_polling_parent_task as parent_status


def test_completed_storyboard_parent_records_video_result(monkeypatch):
    task = SimpleNamespace(
        id=42,
        user_id=7,
        parameters=json.dumps({"script_id": 130}),
        status=TaskStatus.PROCESSING,
        result_file_path=None,
        error_message=None,
    )
    children = [
        SimpleNamespace(
            status=VideoGenerationTaskStatus.SUCCEEDED,
            script_id=130,
            frame_index=0,
            error_message=None,
        )
    ]
    _patch_parent_dependencies(monkeypatch, task)
    db = MagicMock()

    parent_status.refresh_parent_task_status(
        db,
        SimpleNamespace(list_by_task_id=lambda _task_id: children),
        task.id,
    )

    assert task.status is TaskStatus.COMPLETED
    assert task.result_file_path == "storyboard_videos:130:1"
    db.commit.assert_called_once()


def test_failed_storyboard_parent_does_not_record_video_result(monkeypatch):
    task = SimpleNamespace(
        id=43,
        user_id=7,
        parameters=json.dumps({"script_id": 130}),
        status=TaskStatus.PROCESSING,
        result_file_path=None,
        error_message=None,
    )
    children = [
        SimpleNamespace(
            status=VideoGenerationTaskStatus.FAILED,
            script_id=130,
            frame_index=0,
            error_message="provider failed",
        )
    ]
    _patch_parent_dependencies(monkeypatch, task)

    parent_status.refresh_parent_task_status(
        MagicMock(),
        SimpleNamespace(list_by_task_id=lambda _task_id: children),
        task.id,
    )

    assert task.status is TaskStatus.FAILED
    assert task.result_file_path is None
    assert task.error_message == "provider failed"


def test_timeline_rework_parent_does_not_record_storyboard_result(monkeypatch):
    task = SimpleNamespace(
        id=44,
        user_id=7,
        parameters=json.dumps(
            {"script_id": 130, "timeline_rework": {"timeline_id": 11}}
        ),
        status=TaskStatus.PROCESSING,
        result_file_path=None,
        error_message=None,
    )
    children = [
        SimpleNamespace(
            status=VideoGenerationTaskStatus.SUCCEEDED,
            script_id=130,
            frame_index=0,
            error_message=None,
        )
    ]
    _patch_parent_dependencies(monkeypatch, task)

    parent_status.refresh_parent_task_status(
        MagicMock(),
        SimpleNamespace(list_by_task_id=lambda _task_id: children),
        task.id,
    )

    assert task.status is TaskStatus.COMPLETED
    assert task.result_file_path is None


def test_timeline_batch_parent_records_timeline_video_result(monkeypatch):
    task = SimpleNamespace(
        id=45,
        user_id=7,
        parameters=json.dumps(
            {
                "script_id": 130,
                "timeline_id": 71,
                "timeline_version": 6,
                "timeline_rework_by_frame": {"0": {"clip_id": "clip-1"}},
            }
        ),
        status=TaskStatus.PROCESSING,
        result_file_path=None,
        error_message=None,
    )
    children = [
        SimpleNamespace(
            status=VideoGenerationTaskStatus.SUCCEEDED,
            script_id=130,
            frame_index=0,
            error_message=None,
        )
    ]
    _patch_parent_dependencies(monkeypatch, task)

    parent_status.refresh_parent_task_status(
        MagicMock(),
        SimpleNamespace(list_by_task_id=lambda _task_id: children),
        task.id,
    )

    assert task.status is TaskStatus.COMPLETED
    assert task.result_file_path == "timeline_videos:71:v6:1"


def test_parent_waits_for_every_requested_frame_child(monkeypatch):
    task = SimpleNamespace(
        id=46,
        user_id=7,
        parameters=json.dumps({"script_id": 130, "frames": [0, 1]}),
        status=TaskStatus.PROCESSING,
        result_file_path=None,
        error_message=None,
    )
    children = [
        SimpleNamespace(
            status=VideoGenerationTaskStatus.SUCCEEDED,
            script_id=130,
            frame_index=0,
            error_message=None,
        )
    ]
    _patch_parent_dependencies(monkeypatch, task)
    db = MagicMock()

    parent_status.refresh_parent_task_status(
        db,
        SimpleNamespace(list_by_task_id=lambda _task_id: children),
        task.id,
    )

    assert task.status is TaskStatus.PROCESSING
    assert task.result_file_path is None
    db.commit.assert_called_once()


def _patch_parent_dependencies(monkeypatch, task):
    monkeypatch.setattr(
        parent_status,
        "TaskRepository",
        lambda _db: SimpleNamespace(get_by_id=lambda _task_id: task),
    )
    monkeypatch.setattr(parent_status, "persist_task_agent_run", lambda **_kwargs: None)
