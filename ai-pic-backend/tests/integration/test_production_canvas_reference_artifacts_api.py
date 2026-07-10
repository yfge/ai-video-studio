from __future__ import annotations

import json

from app.models.script import Episode, Script, Story
from app.models.story_structure import Environment
from app.models.task import Task
from app.models.user import User
from app.models.virtual_ip import VirtualIP, VirtualIPImage


def _create_script_without_references(db_session, user: User) -> Script:
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
        extra_metadata={
            "storyboard": {
                "frames": [
                    {"description": "林妹妹走进共享办公区"},
                    {"description": "智能音箱开始吐槽代码"},
                ]
            }
        },
    )
    db_session.add(script)
    db_session.commit()
    db_session.refresh(script)
    return script


def test_production_canvas_image_skill_resolves_generated_asset_artifacts(
    client,
    db_session,
    monkeypatch,
):
    user = db_session.query(User).filter(User.username == "test_admin").first()
    script = _create_script_without_references(db_session, user)
    virtual_ip = VirtualIP(user_id=user.id, name="林妹妹", is_active=True)
    environment = Environment(
        user_id=user.id,
        name="共享办公区",
        reference_images=[
            "https://example.com/old-office.png",
            "https://example.com/generated-office.png",
        ],
    )
    db_session.add_all([virtual_ip, environment])
    db_session.commit()
    image = VirtualIPImage(
        virtual_ip_id=virtual_ip.id,
        filename="generated-role.png",
        original_filename="generated-role.png",
        file_path="ai-generated/virtual-ip/generated-role.png",
        oss_url="https://example.com/generated-role.png",
        file_size=128,
        mime_type="image/png",
        category="avatar",
    )
    db_session.add(image)
    db_session.commit()
    db_session.refresh(image)

    dispatched = {}

    def fake_delay(task_id, params, user_id):
        dispatched["task_id"] = task_id
        dispatched["params"] = params
        dispatched["user_id"] = user_id

    monkeypatch.setattr(
        "app.services.storyboard.storyboard_image_autogen."
        "storyboard_image_generate_task.delay",
        fake_delay,
    )

    artifacts = [
        f"virtual_ip_image:{virtual_ip.id}:{image.id}",
        f"environment_images:{environment.id}:1",
    ]
    response = client.post(
        "/api/v1/production-canvas/execute",
        json={
            "prompt": "使用画布生成资产制作分镜候选",
            "skill": "image.candidates",
            "script_id": script.id,
            "frame_indexes": [0, 1],
            "reference_artifacts": artifacts,
            "require_reference_images": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    outputs = payload["skill_result"]["outputs"]
    assert outputs["reference_artifacts"] == artifacts
    assert outputs["reference_image_count"] == 2
    assert outputs["unresolved_reference_artifacts"] == []
    assert outputs["queued_frame_count"] == 2

    task = db_session.get(Task, payload["task_id"])
    params = json.loads(task.parameters)
    assert params["reference_images"] == [
        "https://example.com/generated-role.png",
        "https://example.com/generated-office.png",
    ]
    assert dispatched["params"]["reference_images"] == params["reference_images"]
