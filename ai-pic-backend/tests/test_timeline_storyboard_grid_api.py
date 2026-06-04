import json

from app.models.script import Episode, Script, Story
from app.models.task import Task, TaskType
from app.models.user import User
from sqlalchemy.orm import Session


def _bootstrap_episode(db: Session) -> tuple[User, Episode, Script]:
    user = db.query(User).filter(User.username == "test_admin").first()
    if user is None:
        user = User(
            username="test_admin",
            email="test_admin@example.com",
            hashed_password="test",
            is_active=True,
            is_superuser=True,
            is_admin=True,
            is_approved=True,
            email_verified=True,
        )
        db.add(user)
        db.flush()
    story = Story(title="Grid Storyboard Story", genre="short_drama", user_id=user.id)
    episode = Episode(story=story, episode_number=1, title="Pilot")
    script = Script(
        episode=episode,
        title="Pilot Script",
        content="A: hello",
        scenes=[{"scene_id": "scene_001", "title": "Opening"}],
    )
    db.add_all([story, episode, script])
    db.commit()
    db.refresh(episode)
    db.refresh(script)
    return user, episode, script


def _timeline_spec(episode: Episode, script: Script) -> dict:
    return {
        "spec_version": "timeline.v1",
        "episode_id": episode.id,
        "script_id": script.id,
        "version": 1,
        "source_audio_timeline_version": 1,
        "fps": 24,
        "resolution": "1080x1920",
        "duration_ms": 2400,
        "tracks": [
            {
                "track_type": "dialogue",
                "clips": [
                    {
                        "clip_id": "dialogue_scene_001_beat_001_001",
                        "track_type": "dialogue",
                        "scene_id": "scene_001",
                        "beat_id": "beat_001",
                        "ordinal": 1,
                        "start_ms": 0,
                        "end_ms": 1200,
                        "duration_ms": 1200,
                        "source": {
                            "kind": "audio_timeline_beat",
                            "scene_id": "scene_001",
                            "beat_id": "beat_001",
                            "audio_timeline_version": 1,
                        },
                        "source_refs": {"scene_beat_id": "beat_001"},
                    }
                ],
            }
        ],
    }


def _append_video_clips(spec: dict) -> dict:
    spec["tracks"].append(
        {
            "track_type": "video",
            "clips": [
                {
                    "clip_id": "video_scene_001_beat_001_001",
                    "track_type": "video",
                    "scene_id": "scene_001",
                    "beat_id": "beat_001",
                    "ordinal": 1,
                    "start_ms": 0,
                    "end_ms": 1200,
                    "duration_ms": 1200,
                    "source": {
                        "kind": "audio_timeline_beat",
                        "scene_id": "scene_001",
                        "beat_id": "beat_001",
                        "audio_timeline_version": 1,
                    },
                    "source_refs": {
                        "timeline_shot_plan": {
                            "visual_prompt": "林晚站在雨夜门口，霓虹反光，中景",
                            "video_prompt": "镜头缓慢推近，雨水落在她肩头",
                        }
                    },
                },
                {
                    "clip_id": "video_scene_001_beat_002_001",
                    "track_type": "video",
                    "scene_id": "scene_001",
                    "beat_id": "beat_002",
                    "ordinal": 2,
                    "start_ms": 1200,
                    "end_ms": 2400,
                    "duration_ms": 1200,
                    "source": {
                        "kind": "audio_timeline_beat",
                        "scene_id": "scene_001",
                        "beat_id": "beat_002",
                        "audio_timeline_version": 1,
                    },
                    "source_refs": {},
                    "text": "陈哲坐在车内，侧脸被手机屏照亮。",
                },
            ],
        }
    )
    return spec


def _create_timeline(client, episode: Episode, script: Script, spec: dict) -> dict:
    response = client.post(
        f"/api/v1/episodes/{episode.id}/timelines",
        json={
            "script_id": script.id,
            "title": "Grid Storyboard Timeline",
            "spec": spec,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_timeline_storyboard_grid_endpoint_is_deprecated(client, db_session):
    _, episode, script = _bootstrap_episode(db_session)
    timeline = _create_timeline(
        client,
        episode,
        script,
        _append_video_clips(_timeline_spec(episode, script)),
    )

    response = client.post(
        f"/api/v1/timelines/{timeline['id']}/storyboard-grid/generate",
        json={"expected_version": timeline["version"], "panel_count": 4},
    )

    assert response.status_code == 410
    assert "clips/{clip_id}/storyboard/generate" in response.json()["detail"]


def test_timeline_clip_storyboard_rejects_stale_expected_version(client, db_session):
    _, episode, script = _bootstrap_episode(db_session)
    timeline = _create_timeline(
        client,
        episode,
        script,
        _append_video_clips(_timeline_spec(episode, script)),
    )

    response = client.post(
        "/api/v1/timelines/"
        f"{timeline['id']}/clips/video_scene_001_beat_001_001/storyboard/generate",
        json={"expected_version": timeline["version"] + 1, "panel_count": 4},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "timeline version conflict"


def test_timeline_clip_storyboard_rejects_missing_clip(client, db_session):
    _, episode, script = _bootstrap_episode(db_session)
    timeline = _create_timeline(
        client,
        episode,
        script,
        _append_video_clips(_timeline_spec(episode, script)),
    )

    response = client.post(
        f"/api/v1/timelines/{timeline['id']}/clips/missing_clip/storyboard/generate",
        json={"expected_version": timeline["version"], "panel_count": 4},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "timeline clip not found"


def test_timeline_clip_storyboard_rejects_non_video_clip(client, db_session):
    _, episode, script = _bootstrap_episode(db_session)
    timeline = _create_timeline(client, episode, script, _timeline_spec(episode, script))

    response = client.post(
        "/api/v1/timelines/"
        f"{timeline['id']}/clips/dialogue_scene_001_beat_001_001/storyboard/generate",
        json={"expected_version": timeline["version"], "panel_count": 4},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "clip storyboard requires a video clip"


def test_timeline_clip_storyboard_creates_generation_task_for_selected_clip_only(
    client,
    db_session,
    monkeypatch,
):
    dispatched = {}

    def fake_dispatch(task, payload, current_user):
        dispatched["task_id"] = task.id
        dispatched["payload"] = payload
        dispatched["user_id"] = current_user.id

    monkeypatch.setattr(
        "app.services.storyboard.grid_storyboard_sheet_service."
        "dispatch_grid_storyboard_sheet_task",
        fake_dispatch,
    )
    _, episode, script = _bootstrap_episode(db_session)
    timeline = _create_timeline(
        client,
        episode,
        script,
        _append_video_clips(_timeline_spec(episode, script)),
    )

    response = client.post(
        "/api/v1/timelines/"
        f"{timeline['id']}/clips/video_scene_001_beat_002_001/storyboard/generate",
        json={
            "expected_version": timeline["version"],
            "panel_count": 4,
            "style": "3d_cartoon",
            "model": "openai:gpt-image-2",
            "generation_profile": "clip_storyboard",
        },
    )

    assert response.status_code == 200
    task_id = response.json()["task_id"]
    task = db_session.get(Task, task_id)
    assert task is not None
    assert task.task_type == TaskType.STORYBOARD_IMAGE_GENERATION
    params = json.loads(task.parameters)
    assert params["kind"] == "timeline_clip_storyboard"
    assert params["timeline_id"] == timeline["id"]
    assert params["timeline_version"] == timeline["version"]
    assert params["clip_id"] == "video_scene_001_beat_002_001"
    assert params["generation_profile"] == "clip_storyboard"
    assert params["panel_count"] == 4
    assert params["style"] == "3d_cartoon"
    assert "storyboard sheet" in params["sheet_prompt"].lower()
    assert len(params["panels"]) == 4
    assert {panel["clip_id"] for panel in params["panels"]} == {
        "video_scene_001_beat_002_001"
    }
    assert dispatched["task_id"] == task_id
    assert dispatched["payload"]["clip_id"] == "video_scene_001_beat_002_001"
