from __future__ import annotations

import json

from app.models.script import Episode, Script, Story
from app.models.task import Task, TaskType
from app.models.user import User


def _create_script_context(db_session, user: User) -> Script:
    story = Story(user_id=user.id, title="程序员轻喜剧", genre="comedy")
    db_session.add(story)
    db_session.commit()
    episode = Episode(story_id=story.id, episode_number=4, title="智能生活入门")
    db_session.add(episode)
    db_session.commit()
    script = Script(
        episode_id=episode.id,
        title="第 4 集剧本",
        content="办公室轻喜剧",
    )
    db_session.add(script)
    db_session.commit()
    db_session.refresh(script)
    return script


def test_production_canvas_execute_timeline_skill_dispatches_existing_task(
    client,
    db_session,
    monkeypatch,
):
    user = db_session.query(User).filter(User.username == "test_admin").first()
    script = _create_script_context(db_session, user)
    dispatched = {}

    def fake_delay(task_id, params, user_id):
        dispatched["task_id"] = task_id
        dispatched["params"] = params
        dispatched["user_id"] = user_id

    monkeypatch.setattr(
        "app.services.script.timeline_pipeline_queue.timeline_pipeline_generate_task.delay",
        fake_delay,
    )
    response = client.post(
        "/api/v1/production-canvas/execute",
        json={
            "prompt": "组装现有剧本时间线",
            "skill": "timeline.assemble",
            "script_id": script.id,
            "run_id": "abcdabcdabcdabcdabcdabcdabcdabcd",
        },
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["task_id"]
    assert payload["task_status"] == "pending"
    assert payload["skill_result"]["skill"] == "timeline.assemble"
    assert payload["skill_result"]["status"] == "running"
    assert payload["skill_result"]["outputs"]["script_id"] == script.id
    assert (
        payload["skill_result"]["outputs"]["dispatched_task_id"] == payload["task_id"]
    )

    task = db_session.get(Task, payload["task_id"])
    assert task.task_type == TaskType.TIMELINE_PIPELINE
    assert task.target_business_id == "abcdabcdabcdabcdabcdabcdabcdabcd"
    params = json.loads(task.parameters)
    assert params["script_id"] == script.id
    assert params["overwrite_audio"] is False
    assert params["overwrite_timeline"] is False
    assert params["overwrite_storyboard"] is True
    assert dispatched["task_id"] == task.id
    assert dispatched["params"]["script_id"] == script.id
    assert dispatched["params"]["overwrite_storyboard"] is True
