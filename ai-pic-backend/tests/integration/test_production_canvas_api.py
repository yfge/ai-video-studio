from __future__ import annotations

import json

from app.models.script import Episode, Script, Story
from app.models.story_structure import Environment
from app.models.task import Task, TaskStatus, TaskType
from app.models.user import User
from app.models.virtual_ip import VirtualIP, VirtualIPEnvironment


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


def test_production_canvas_plan_api_reuses_ip_environment_assets(client, db_session):
    user = db_session.query(User).filter(User.username == "test_admin").first()
    virtual_ip = VirtualIP(
        user_id=user.id,
        name="林妹妹",
        description="程序员身边的轻喜剧女主",
        is_active=True,
    )
    environment = Environment(
        user_id=user.id,
        name="共享办公区",
        category="indoor",
        reference_images=["https://example.test/office.png"],
    )
    db_session.add_all([virtual_ip, environment])
    db_session.commit()
    db_session.refresh(virtual_ip)
    db_session.refresh(environment)
    db_session.add(
        VirtualIPEnvironment(
            user_id=user.id,
            virtual_ip_id=virtual_ip.id,
            virtual_ip_business_id=virtual_ip.business_id,
            environment_id=environment.id,
            environment_business_id=environment.business_id,
            usage_type="main_scene",
            is_default=True,
        )
    )
    db_session.commit()

    response = client.post(
        "/api/v1/production-canvas/plan",
        json={"prompt": "基于林妹妹做第 4 集，办公室轻喜剧"},
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["skill_manifest"]["version"] == "production_canvas.v1"
    assert payload["skill_manifest"]["skills"][0]["id"] == "brief.compose"
    assert payload["selected_assets"]["virtual_ips"][0]["name"] == "林妹妹"
    assert payload["selected_assets"]["environments"][0]["name"] == "共享办公区"
    assert payload["skill_results"][1]["skill"] == "asset.select"
    script_result = next(
        result
        for result in payload["skill_results"]
        if result["skill"] == "script.generate"
    )
    assert script_result["reuse_targets"][0]["target"].endswith("generate_script_async")
    assert payload["task_id"]
    assert payload["run_id"]
    assert payload["nodes"][1]["skill"] == "asset.select"
    assert payload["nodes"][1]["reuse_targets"][0]["kind"] == "repository"
    task = db_session.get(Task, payload["task_id"])
    assert task is not None
    assert task.business_id == payload["run_id"]
    assert task.task_type == TaskType.TEXT_GENERATION
    assert task.status == TaskStatus.COMPLETED
    assert task.result_file_path == f"production_canvas:{payload['run_id']}"
    params = json.loads(task.parameters)
    assert params["kind"] == "production_canvas_run"
    assert params["prompt"] == "基于林妹妹做第 4 集，办公室轻喜剧"
    assert params["skill_results"][1]["skill"] == "asset.select"
    assert params["selected_assets"]["virtual_ips"][0]["name"] == "林妹妹"


def test_production_canvas_execute_script_skill_dispatches_existing_task(
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
        "app.services.script.generation_queue.script_generate_task.delay",
        fake_delay,
    )

    response = client.post(
        "/api/v1/production-canvas/execute",
        json={
            "prompt": "基于林妹妹做第 4 集，办公室轻喜剧",
            "skill": "script.generate",
            "episode_id": script.episode_id,
            "run_id": "abcdabcdabcdabcdabcdabcdabcdabcd",
        },
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["task_id"]
    assert payload["task_status"] == "pending"
    assert payload["skill_result"]["skill"] == "script.generate"
    assert payload["skill_result"]["status"] == "running"
    assert (
        payload["skill_result"]["outputs"]["dispatched_task_id"] == payload["task_id"]
    )
    assert payload["skill_result"]["outputs"]["canvas_run_id"] == (
        "abcdabcdabcdabcdabcdabcdabcdabcd"
    )

    task = db_session.get(Task, payload["task_id"])
    assert task is not None
    assert task.task_type == TaskType.SCRIPT_GENERATION
    assert task.target_business_id == "abcdabcdabcdabcdabcdabcdabcdabcd"
    params = json.loads(task.parameters)
    assert params["episode_id"] == script.episode_id
    assert params["generation_mode"] == "production"
    assert params["auto_timeline_pipeline"] is True
    assert params["additional_requirements"] == "基于林妹妹做第 4 集，办公室轻喜剧"
    assert dispatched["task_id"] == task.id
    assert dispatched["params"]["episode_id"] == script.episode_id


def test_production_canvas_execute_rejects_mixed_story_episode_lineage(
    client,
    db_session,
    monkeypatch,
):
    user = db_session.query(User).filter(User.username == "test_admin").first()
    first_script = _create_script_context(db_session, user)
    second_script = _create_script_context(db_session, user)
    dispatched = []
    monkeypatch.setattr(
        "app.services.script.generation_queue.script_generate_task.delay",
        lambda *args, **kwargs: dispatched.append((args, kwargs)),
    )

    response = client.post(
        "/api/v1/production-canvas/execute",
        json={
            "prompt": "不要混用两个故事的上下文",
            "skill": "script.generate",
            "story_id": first_script.episode.story_id,
            "episode_id": second_script.episode_id,
        },
    )

    assert response.status_code == 400
    assert response.json()["message"] == "story_id 与上游业务上下文不一致"
    assert dispatched == []


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
