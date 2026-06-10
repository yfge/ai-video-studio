import json

from app.models.task import Task, TaskStatus, TaskType
from tests.test_timeline_clip_video_grid_rework_api import (
    _bootstrap_episode,
    _create_timeline,
    _timeline_spec_with_video_clip,
)


def _add_task(
    db_session,
    user,
    *,
    target_business_id,
    status=TaskStatus.PENDING,
    parameters=None,
    title="Timeline clip rework - clip",
):
    task = Task(
        title=title,
        description="clip task",
        task_type=TaskType.VIDEO_GENERATION,
        status=status,
        prompt="prompt",
        parameters=parameters,
        target_business_id=target_business_id,
        user_id=user.id,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


def test_list_timeline_clip_tasks_returns_active_tasks_with_clip_ids(
    client, db_session
):
    user, episode, script = _bootstrap_episode(db_session)
    clip_id = "video_scene_001_beat_001_001"
    timeline = _create_timeline(
        client,
        episode,
        script,
        _timeline_spec_with_video_clip(episode, script, clip_id),
    )
    timeline_business_id = timeline["business_id"]

    pending = _add_task(
        db_session,
        user,
        target_business_id=timeline_business_id,
        parameters=json.dumps({"clip_id": clip_id, "timeline_id": timeline["id"]}),
    )
    processing = _add_task(
        db_session,
        user,
        target_business_id=timeline_business_id,
        status=TaskStatus.PROCESSING,
        parameters="not-json",
    )
    _add_task(
        db_session,
        user,
        target_business_id=timeline_business_id,
        status=TaskStatus.COMPLETED,
        parameters=json.dumps({"clip_id": clip_id}),
    )
    _add_task(
        db_session,
        user,
        target_business_id="some-other-target",
        parameters=json.dumps({"clip_id": clip_id}),
    )

    response = client.get(f"/api/v1/timelines/{timeline['id']}/clip-tasks")

    assert response.status_code == 200, response.text
    items = response.json()["items"]
    assert [item["task_id"] for item in items] == [processing.id, pending.id]
    by_id = {item["task_id"]: item for item in items}
    assert by_id[pending.id]["clip_id"] == clip_id
    assert by_id[pending.id]["status"] == "pending"
    assert by_id[processing.id]["clip_id"] is None
    assert by_id[processing.id]["status"] == "processing"
    assert by_id[processing.id]["task_type"] == "video_generation"


def test_list_timeline_clip_tasks_404_for_unknown_timeline(client, db_session):
    _bootstrap_episode(db_session)
    response = client.get("/api/v1/timelines/999999/clip-tasks")
    assert response.status_code == 404
