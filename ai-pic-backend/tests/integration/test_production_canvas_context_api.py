from __future__ import annotations

import json

from app.models.script import Episode, Story, StoryCharacter
from app.models.task import Task, TaskStatus, TaskType
from app.models.user import User
from app.models.virtual_ip import VirtualIP


def test_canvas_plan_api_persists_resolved_hierarchy_context(client, db_session):
    user = db_session.query(User).filter(User.username == "test_admin").first()
    virtual_ip = VirtualIP(
        user_id=user.id,
        name="林妹妹",
        is_active=True,
    )
    story = Story(
        user_id=user.id,
        title="林妹妹办公室故事",
        genre="comedy",
    )
    db_session.add_all([virtual_ip, story])
    db_session.commit()
    episode = Episode(
        story_id=story.id,
        episode_number=4,
        title="智能生活入门",
    )
    db_session.add_all(
        [
            StoryCharacter(
                story_id=story.id,
                virtual_ip_id=virtual_ip.id,
                character_name="林妹妹",
            ),
            episode,
        ]
    )
    db_session.commit()

    response = client.post(
        "/api/v1/production-canvas/plan",
        json={"prompt": "基于林妹妹做第 4 集，生成完整短剧链路"},
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["resolved_context"]["virtual_ip_id"] == virtual_ip.id
    assert payload["resolved_context"]["story_id"] == story.id
    assert payload["resolved_context"]["episode_id"] == episode.id
    task = db_session.get(Task, payload["task_id"])
    assert task is not None
    parameters = json.loads(task.parameters)
    assert parameters["resolved_context"]["story_id"] == story.id
    assert parameters["requested_asset_ids"]["episode_id"] == episode.id
    script_result = next(
        item
        for item in parameters["skill_results"]
        if item["skill"] == "script.generate"
    )
    assert script_result["outputs"]["story_id"] == story.id
    assert script_result["outputs"]["episode_id"] == episode.id


def test_canvas_plan_api_rejects_unknown_task_context(client):
    response = client.post(
        "/api/v1/production-canvas/plan",
        json={"prompt": "继续不存在的任务", "task_id": 999_999_999},
    )

    assert response.status_code == 404
    assert response.json()["message"] == "Task不存在: 999999999"


def test_canvas_plan_api_rejects_foreign_task_context(client, db_session):
    other = User(
        username="canvas_foreign_task_owner",
        email="canvas_foreign_task_owner@example.com",
        hashed_password="x",
        is_active=True,
        is_approved=True,
        email_verified=True,
    )
    db_session.add(other)
    db_session.commit()
    task = Task(
        title="其他用户的任务",
        task_type=TaskType.TEXT_GENERATION,
        status=TaskStatus.COMPLETED,
        parameters="{}",
        user_id=other.id,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    response = client.post(
        "/api/v1/production-canvas/plan",
        json={"prompt": "尝试接管其他用户任务", "task_id": task.id},
    )

    assert response.status_code == 404
    assert response.json()["message"] == f"Task不存在: {task.id}"
