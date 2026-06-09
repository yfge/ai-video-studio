import json

from app.models.episode_character import EpisodeCharacter
from app.models.task import Task
from app.models.virtual_ip import VirtualIP, VirtualIPImage
from sqlalchemy.orm import Session
from tests.test_timeline_clip_video_grid_rework_api import (
    _bootstrap_episode,
    _create_timeline,
    _timeline_spec_with_video_clip,
)


def test_timeline_clip_video_rework_binds_character_and_environment_context(
    client, db_session, monkeypatch
):
    dispatched = {}

    def fake_dispatch(task, payload, current_user):
        dispatched["task_id"] = task.id
        dispatched["payload"] = payload
        dispatched["user_id"] = current_user.id

    monkeypatch.setattr(
        "app.services.timeline_clip_video_rework_queue_service."
        "dispatch_timeline_clip_video_rework_task",
        fake_dispatch,
    )
    user, episode, script = _bootstrap_episode(db_session)
    virtual_ip = _add_episode_character(db_session, episode.id, user.id, "快递员")
    clip_id = "video_scene_001_beat_001_001"
    timeline = _create_timeline(
        client,
        episode,
        script,
        _timeline_spec_with_video_clip(episode, script, clip_id),
    )

    response = client.post(
        f"/api/v1/timelines/{timeline['id']}/clips/{clip_id}/rework/video",
        json={
            "expected_version": timeline["version"],
            "action": "re_cut",
            "prompt": "保持动作连贯",
            "character_virtual_ip_ids": [virtual_ip.id],
            "character_reference_images": ["https://selected.example/ip.png"],
            "environment_reference_images": ["https://selected.example/env.png"],
            "reference_images": ["https://manual.example/ref.png"],
        },
    )

    assert response.status_code == 200, response.text
    params = json.loads(db_session.get(Task, response.json()["task_id"]).parameters)
    assert params["character_virtual_ip_ids"] == [virtual_ip.id]
    assert params["character_reference_images"] == ["https://selected.example/ip.png"]
    assert params["environment_reference_images"] == [
        "https://selected.example/env.png"
    ]
    assert params["reference_images"] == [
        "https://selected.example/ip.png",
        "https://selected.example/env.png",
        "https://manual.example/ref.png",
        "https://cdn.example/courier.png",
    ]
    assert params["bound_context"]["characters"] == [
        {
            "name": "快递员",
            "virtual_ip_id": virtual_ip.id,
            "anchor_url": "https://cdn.example/courier.png",
        }
    ]
    assert dispatched["payload"]["reference_images"] == params["reference_images"]
    assert dispatched["payload"]["bound_context"] == params["bound_context"]


def _add_episode_character(
    db: Session,
    episode_id: int,
    user_id: int,
    name: str,
) -> VirtualIP:
    virtual_ip = VirtualIP(
        user_id=user_id,
        name=name,
        description=f"{name} character profile",
        style_prompt=f"{name} visual style",
    )
    db.add(virtual_ip)
    db.flush()
    db.add(
        VirtualIPImage(
            virtual_ip_id=virtual_ip.id,
            filename="courier.png",
            original_filename="courier.png",
            file_path="/uploads/courier.png",
            oss_url="https://cdn.example/courier.png",
            file_size=123,
            mime_type="image/png",
            category="avatar",
            is_default=True,
        )
    )
    db.add(
        EpisodeCharacter(
            episode_id=episode_id,
            virtual_ip_id=virtual_ip.id,
            character_name=name,
            role_type="temporary",
            importance=3,
        )
    )
    db.commit()
    db.refresh(virtual_ip)
    return virtual_ip
