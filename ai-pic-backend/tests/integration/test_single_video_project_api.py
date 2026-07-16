from __future__ import annotations

import json

from app.models.script import Episode, Story, StoryCharacter
from app.models.story_structure import Environment
from app.models.task import Task, TaskType
from app.models.user import User
from app.models.virtual_ip import VirtualIP, VirtualIPEnvironment


def test_single_video_project_creates_internal_story_episode_without_task(
    client,
    db_session,
):
    response = client.post(
        "/api/v1/stories/single-video",
        json={
            "title": "三分钟产品介绍",
            "prompt": "用轻快节奏介绍一款桌面机器人",
            "duration_minutes": 3,
            "aspect_ratio": "16:9",
            "style": "明亮科技感",
            "start_generation": False,
        },
    )

    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["task_id"] is None
    assert payload["context"]["story_id"] == payload["story_id"]
    assert payload["context"]["episode_id"] == payload["episode_id"]

    story = db_session.get(Story, payload["story_id"])
    episode = db_session.get(Episode, payload["episode_id"])
    assert story is not None
    assert episode is not None
    assert story.genre == "single_video"
    assert story.extra_metadata["creation_mode"] == "single_video"
    assert story.extra_metadata["system_managed_hierarchy"] is True
    assert story.extra_metadata["episode_id"] == episode.id
    assert episode.episode_number == 1
    assert episode.duration_minutes == 3
    assert episode.aspect_ratio == "16:9"


def test_single_video_project_reuses_assets_and_queues_existing_script_pipeline(
    client,
    db_session,
    monkeypatch,
):
    user = db_session.query(User).filter(User.username == "test_admin").first()
    virtual_ip = VirtualIP(
        user_id=user.id,
        name="林晚",
        description="桌面机器人产品经理",
        is_active=True,
    )
    environment = Environment(
        user_id=user.id,
        name="产品演示间",
        category="indoor",
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
        )
    )
    db_session.commit()
    dispatched = {}

    def fake_delay(task_id, params, user_id):
        dispatched.update(task_id=task_id, params=params, user_id=user_id)

    monkeypatch.setattr(
        "app.services.script.generation_queue.script_generate_task.delay",
        fake_delay,
    )

    response = client.post(
        "/api/v1/stories/single-video",
        json={
            "title": "五分钟人物短片",
            "prompt": "林晚在产品演示间完成一次有反转的产品发布",
            "duration_minutes": 5,
            "virtual_ip_id": virtual_ip.id,
            "environment_id": environment.id,
        },
    )

    assert response.status_code == 201, response.text
    payload = response.json()
    task = db_session.get(Task, payload["task_id"])
    assert task is not None
    assert task.task_type == TaskType.SCRIPT_GENERATION
    assert task.target_business_id == payload["episode_business_id"]
    params = json.loads(task.parameters)
    assert params["generation_mode"] == "production"
    assert params["auto_timeline_pipeline"] is True
    assert params["target_chars_per_episode"] == 1500
    assert "成片总时长：5 分钟" in params["additional_requirements"]
    assert "其他成片时长不生效" in params["additional_requirements"]
    assert dispatched["task_id"] == task.id
    assert dispatched["params"]["episode_id"] == payload["episode_id"]
    assert payload["context"]["virtual_ip_id"] == virtual_ip.id
    assert payload["context"]["environment_id"] == environment.id

    character = (
        db_session.query(StoryCharacter)
        .filter(StoryCharacter.story_id == payload["story_id"])
        .one()
    )
    assert character.virtual_ip_id == virtual_ip.id
    story = db_session.get(Story, payload["story_id"])
    assert story.extra_metadata["script_task_id"] == task.id


def test_single_video_project_rejects_unlinked_ip_environment_pair(
    client,
    db_session,
):
    user = db_session.query(User).filter(User.username == "test_admin").first()
    virtual_ip = VirtualIP(user_id=user.id, name="未关联角色", is_active=True)
    environment = Environment(user_id=user.id, name="未关联环境")
    db_session.add_all([virtual_ip, environment])
    db_session.commit()

    response = client.post(
        "/api/v1/stories/single-video",
        json={
            "title": "不应创建",
            "prompt": "测试资源关系",
            "virtual_ip_id": virtual_ip.id,
            "environment_id": environment.id,
            "start_generation": False,
        },
    )

    assert response.status_code == 400
    assert "不属于指定" in response.json()["message"]
    assert db_session.query(Story).filter(Story.title == "不应创建").count() == 0


def test_single_video_canvas_plan_does_not_guess_prompt_assets(
    client,
    db_session,
    monkeypatch,
):
    user = db_session.query(User).filter(User.username == "test_admin").first()
    db_session.add(VirtualIP(user_id=user.id, name="林妹妹", is_active=True))
    db_session.commit()
    project_response = client.post(
        "/api/v1/stories/single-video",
        json={
            "title": "无 IP 的单条视频",
            "prompt": "基于林妹妹做一分钟办公短剧",
            "start_generation": False,
        },
    )
    project = project_response.json()

    response = client.post(
        "/api/v1/production-canvas/plan",
        json={
            "prompt": "基于林妹妹做一分钟办公短剧",
            "planning_mode": "single_video",
            "story_id": project["story_id"],
            "episode_id": project["episode_id"],
        },
    )

    assert response.status_code == 200, response.text
    plan = response.json()["data"]
    assert plan["selected_assets"]["virtual_ips"] == []
    assert plan["resolved_context"].get("virtual_ip_id") is None
    script_node = next(
        node for node in plan["nodes"] if node["skill"] == "script.generate"
    )
    assert script_node["status"] == "ready"

    dispatched = {}
    monkeypatch.setattr(
        "app.services.script.generation_queue.script_generate_task.delay",
        lambda task_id, params, user_id: dispatched.update(
            task_id=task_id,
            params=params,
            user_id=user_id,
        ),
    )
    execution_response = client.post(
        "/api/v1/production-canvas/execute",
        json={
            "prompt": "基于林妹妹做一分钟办公短剧",
            "skill": "script.generate",
            "story_id": project["story_id"],
            "episode_id": project["episode_id"],
            "run_id": plan["run_id"],
        },
    )

    assert execution_response.status_code == 200, execution_response.text
    task = db_session.get(Task, execution_response.json()["data"]["task_id"])
    params = json.loads(task.parameters)
    requirements = params["additional_requirements"]
    assert params["target_chars_per_episode"] == 900
    assert requirements.startswith("## 系统生产约束（优先级最高）")
    assert "成片总时长：3 分钟" in requirements
    assert "其他成片时长不生效" in requirements
    assert requirements.index("成片总时长：3 分钟") < requirements.index(
        "基于林妹妹做一分钟办公短剧"
    )
    assert dispatched["params"]["target_chars_per_episode"] == 900
