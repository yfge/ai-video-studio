import json

from app.models.episode_character import EpisodeCharacter
from app.models.script import StoryCharacter
from app.models.task import Task
from app.models.virtual_ip import VirtualIP, VirtualIPImage
from sqlalchemy.orm import Session
from tests.test_timeline_storyboard_grid_api import (
    _append_video_clips,
    _bootstrap_episode,
    _create_timeline,
    _timeline_spec,
)


def test_timeline_clip_storyboard_auto_binds_character_reference_images(
    client,
    db_session,
    monkeypatch,
):
    dispatched = {}

    def fake_dispatch(task, payload, current_user):
        dispatched["payload"] = payload

    monkeypatch.setattr(
        "app.services.storyboard.grid_storyboard_sheet_service."
        "dispatch_grid_storyboard_sheet_task",
        fake_dispatch,
    )
    user, episode, script = _bootstrap_episode(db_session)
    virtual_ip = _add_story_character(db_session, episode.story_id, user.id, "林晚")
    spec = _append_video_clips(_timeline_spec(episode, script))
    spec["tracks"][0]["clips"][0]["speaker_name"] = "林晚"
    timeline = _create_timeline(client, episode, script, spec)

    response = client.post(
        "/api/v1/timelines/"
        f"{timeline['id']}/clips/video_scene_001_beat_001_001/storyboard/generate",
        json={
            "expected_version": timeline["version"],
            "panel_count": 4,
            "reference_images": ["https://manual.example/ref.png"],
        },
    )

    assert response.status_code == 200, response.text
    params = json.loads(db_session.get(Task, response.json()["task_id"]).parameters)
    assert params["reference_images"] == [
        "https://manual.example/ref.png",
        "https://cdn.example/linwan.png",
    ]
    assert params["bound_context"]["characters"] == [
        {
            "name": "林晚",
            "virtual_ip_id": virtual_ip.id,
            "anchor_url": "https://cdn.example/linwan.png",
        }
    ]
    assert params["panels"][0]["bound_context"] == params["bound_context"]
    assert dispatched["payload"]["reference_images"] == params["reference_images"]


def test_timeline_clip_storyboard_binds_episode_character_ip_from_clip_metadata(
    client,
    db_session,
    monkeypatch,
):
    dispatched = {}

    def fake_dispatch(task, payload, current_user):
        dispatched["payload"] = payload

    monkeypatch.setattr(
        "app.services.storyboard.grid_storyboard_sheet_service."
        "dispatch_grid_storyboard_sheet_task",
        fake_dispatch,
    )
    user, episode, script = _bootstrap_episode(db_session)
    virtual_ip = _add_episode_character(db_session, episode.id, user.id, "快递员")
    spec = _append_video_clips(_timeline_spec(episode, script))
    video_clip = spec["tracks"][1]["clips"][0]
    video_clip["source_refs"]["virtual_ip_id"] = virtual_ip.id
    timeline = _create_timeline(client, episode, script, spec)

    response = client.post(
        "/api/v1/timelines/"
        f"{timeline['id']}/clips/video_scene_001_beat_001_001/storyboard/generate",
        json={"expected_version": timeline["version"], "panel_count": 4},
    )

    assert response.status_code == 200, response.text
    params = json.loads(db_session.get(Task, response.json()["task_id"]).parameters)
    assert params["reference_images"] == ["https://cdn.example/courier.png"]
    assert params["bound_context"]["characters"] == [
        {
            "name": "快递员",
            "virtual_ip_id": virtual_ip.id,
            "anchor_url": "https://cdn.example/courier.png",
        }
    ]
    assert dispatched["payload"]["bound_context"] == params["bound_context"]


def test_timeline_clip_storyboard_binds_request_character_ip_selection(
    client,
    db_session,
    monkeypatch,
):
    dispatched = {}

    def fake_dispatch(task, payload, current_user):
        dispatched["payload"] = payload

    monkeypatch.setattr(
        "app.services.storyboard.grid_storyboard_sheet_service."
        "dispatch_grid_storyboard_sheet_task",
        fake_dispatch,
    )
    user, episode, script = _bootstrap_episode(db_session)
    _add_story_character(db_session, episode.story_id, user.id, "林晚")
    virtual_ip = _add_episode_character(db_session, episode.id, user.id, "快递员")
    spec = _append_video_clips(_timeline_spec(episode, script))
    video_clip = spec["tracks"][1]["clips"][0]
    video_clip["text"] = "林晚打开门，接过快递员递来的包裹。"
    timeline = _create_timeline(client, episode, script, spec)

    response = client.post(
        "/api/v1/timelines/"
        f"{timeline['id']}/clips/video_scene_001_beat_001_001/storyboard/generate",
        json={
            "expected_version": timeline["version"],
            "panel_count": 4,
            "character_virtual_ip_ids": [virtual_ip.id],
        },
    )

    assert response.status_code == 200, response.text
    params = json.loads(db_session.get(Task, response.json()["task_id"]).parameters)
    assert params["character_virtual_ip_ids"] == [virtual_ip.id]
    assert params["reference_images"] == ["https://cdn.example/courier.png"]
    assert params["bound_context"]["characters"] == [
        {
            "name": "快递员",
            "virtual_ip_id": virtual_ip.id,
            "anchor_url": "https://cdn.example/courier.png",
        }
    ]
    assert dispatched["payload"]["character_virtual_ip_ids"] == [virtual_ip.id]
    assert dispatched["payload"]["bound_context"] == params["bound_context"]


def _add_story_character(
    db: Session,
    story_id: int,
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
            filename="linwan.png",
            original_filename="linwan.png",
            file_path="/uploads/linwan.png",
            oss_url="https://cdn.example/linwan.png",
            file_size=123,
            mime_type="image/png",
            category="avatar",
            is_default=True,
        )
    )
    db.add(
        StoryCharacter(
            story_id=story_id,
            virtual_ip_id=virtual_ip.id,
            character_name=name,
            role_type="protagonist",
            importance=5,
        )
    )
    db.commit()
    db.refresh(virtual_ip)
    return virtual_ip


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
