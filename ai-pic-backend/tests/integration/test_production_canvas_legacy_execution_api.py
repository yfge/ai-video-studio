from __future__ import annotations

import json

from app.models.task import Task, TaskType
from app.models.user import User
from tests.integration.test_production_canvas_api import _create_script_context


def test_production_canvas_execute_script_skill_blocks_without_episode(
    client,
    monkeypatch,
):
    calls = []

    def fake_delay(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr(
        "app.services.script.generation_queue.script_generate_task.delay",
        fake_delay,
    )

    response = client.post(
        "/api/v1/production-canvas/execute",
        json={
            "prompt": "基于林妹妹做第 4 集，办公室轻喜剧",
            "skill": "script.generate",
        },
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["task_id"] is None
    assert payload["task_status"] is None
    assert payload["skill_result"]["status"] == "blocked"
    assert payload["skill_result"]["outputs"]["required_inputs"] == ["episode_id"]
    assert calls == []


def test_production_canvas_execute_storyboard_skill_dispatches_existing_task(
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
        "app.services.storyboard.generation_queue.storyboard_generate_task.delay",
        fake_delay,
    )

    response = client.post(
        "/api/v1/production-canvas/execute",
        json={
            "prompt": "继续现有剧本生成分镜",
            "skill": "storyboard.plan",
            "script_id": script.id,
            "run_id": "abcdabcdabcdabcdabcdabcdabcdabcd",
        },
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["task_id"]
    assert payload["task_status"] == "pending"
    assert payload["skill_result"]["skill"] == "storyboard.plan"
    assert payload["skill_result"]["status"] == "running"
    assert payload["skill_result"]["outputs"]["script_id"] == script.id
    assert (
        payload["skill_result"]["outputs"]["dispatched_task_id"] == payload["task_id"]
    )

    task = db_session.get(Task, payload["task_id"])
    assert task.task_type == TaskType.STORYBOARD_GENERATION
    assert task.target_business_id == "abcdabcdabcdabcdabcdabcdabcdabcd"
    params = json.loads(task.parameters)
    assert params["script_id"] == script.id
    assert params["use_plan"] is True
    assert dispatched["task_id"] == task.id
    assert dispatched["params"]["script_id"] == script.id
