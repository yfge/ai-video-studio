import json

from app.models.task import Task, TaskStatus, TaskType
from app.services.script.regeneration_task_helpers import update_task_status
from tests.test_timeline_clip_video_grid_rework_api import _bootstrap_episode


def _add_task(db_session, user, *, status=TaskStatus.PENDING):
    task = Task(
        title="生成剧本 - 测试",
        description="detail",
        task_type=TaskType.SCRIPT_GENERATION,
        status=status,
        prompt="prompt",
        parameters=json.dumps({}),
        user_id=user.id,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


def test_cancel_pending_task(client, db_session):
    user, _, _ = _bootstrap_episode(db_session)
    task = _add_task(db_session, user)

    response = client.post(f"/api/v1/tasks/{task.id}/cancel")

    assert response.status_code == 200, response.text
    assert response.json()["data"]["status"] == "cancelled"
    db_session.refresh(task)
    assert task.status == TaskStatus.CANCELLED
    assert task.error_message == "已被用户取消"


def test_cancel_processing_task_best_effort(client, db_session):
    user, _, _ = _bootstrap_episode(db_session)
    task = _add_task(db_session, user, status=TaskStatus.PROCESSING)

    response = client.post(f"/api/v1/tasks/{task.id}/cancel")

    assert response.status_code == 200, response.text
    db_session.refresh(task)
    assert task.status == TaskStatus.CANCELLED


def test_cancel_completed_task_rejected(client, db_session):
    user, _, _ = _bootstrap_episode(db_session)
    task = _add_task(db_session, user, status=TaskStatus.COMPLETED)

    response = client.post(f"/api/v1/tasks/{task.id}/cancel")

    assert response.status_code == 400


def test_cancel_unknown_task_404(client, db_session):
    _bootstrap_episode(db_session)
    response = client.post("/api/v1/tasks/999999/cancel")
    assert response.status_code == 404


def test_worker_status_writer_does_not_resurrect_cancelled_task(
    client, db_session
):
    user, _, _ = _bootstrap_episode(db_session)
    task = _add_task(db_session, user, status=TaskStatus.PROCESSING)
    client.post(f"/api/v1/tasks/{task.id}/cancel")

    update_task_status(
        db_session,
        task.id,
        status=TaskStatus.COMPLETED,
        result_file_path="script:1",
    )

    db_session.refresh(task)
    assert task.status == TaskStatus.CANCELLED
    assert task.result_file_path != "script:1"
