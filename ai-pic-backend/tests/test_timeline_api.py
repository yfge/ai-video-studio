from app.core.middleware import get_current_active_user
from app.main import app
from app.models.script import Episode, Script, Story
from app.models.timeline import RenderJob
from app.models.user import User
from app.services.timeline_service import TimelineService
from sqlalchemy.orm import Session


def _bootstrap_episode(db: Session) -> tuple[Episode, Script]:
    user = db.query(User).filter(User.username == "test_admin").one()
    story = Story(
        title="Timeline Story",
        genre="short_drama",
        user_id=user.id,
    )
    episode = Episode(
        story=story,
        episode_number=1,
        title="Pilot",
        duration_minutes=3,
    )
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
    return episode, script


def _timeline_spec(episode: Episode, script: Script, version: int = 1) -> dict:
    return {
        "spec_version": "timeline.v1",
        "episode_id": episode.id,
        "script_id": script.id,
        "version": version,
        "source_audio_timeline_version": 1,
        "fps": 24,
        "resolution": "1080x1920",
        "duration_ms": 1200,
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
                        "source_refs": {
                            "scene_beat_id": "beat_001",
                            "audio_timeline_version": 1,
                        },
                    }
                ],
            }
        ],
    }


def test_timeline_crud_version_lock_and_render_idempotency(
    client,
    db_session,
    monkeypatch,
):
    monkeypatch.setattr(
        TimelineService,
        "_dispatch_render_job",
        staticmethod(lambda _job, _user: None),
    )
    episode, script = _bootstrap_episode(db_session)

    create_response = client.post(
        f"/api/v1/episodes/{episode.id}/timelines",
        json={
            "script_id": script.id,
            "title": "Pilot Main Timeline",
            "spec": _timeline_spec(episode, script),
            "source_audio_timeline_version": 1,
        },
    )
    assert create_response.status_code == 200
    timeline = create_response.json()
    assert timeline["episode_id"] == episode.id
    assert timeline["script_id"] == script.id
    assert timeline["version"] == 1

    list_response = client.get(f"/api/v1/episodes/{episode.id}/timelines")
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()["items"]] == [timeline["id"]]

    read_response = client.get(f"/api/v1/timelines/{timeline['id']}")
    assert read_response.status_code == 200
    assert read_response.json()["business_id"] == timeline["business_id"]

    updated_spec = _timeline_spec(episode, script, version=2)
    updated_spec["duration_ms"] = 1400
    updated_spec["tracks"][0]["clips"][0]["end_ms"] = 1400
    updated_spec["tracks"][0]["clips"][0]["duration_ms"] = 1400
    update_response = client.patch(
        f"/api/v1/timelines/{timeline['id']}",
        json={
            "expected_version": 1,
            "status": "ready",
            "spec": updated_spec,
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["version"] == 2
    assert updated["status"] == "ready"
    assert updated["spec"]["tracks"][0]["clips"][0]["duration_ms"] == 1400

    conflict_response = client.patch(
        f"/api/v1/timelines/{timeline['id']}",
        json={"expected_version": 1, "status": "locked"},
    )
    assert conflict_response.status_code == 409

    stale_render_response = client.post(
        f"/api/v1/timelines/{timeline['id']}/render",
        json={
            "timeline_version": 1,
            "render_type": "proxy",
            "preset": {"resolution": "720p", "fps": 24},
        },
    )
    assert stale_render_response.status_code == 409

    render_payload = {
        "timeline_version": 2,
        "render_type": "proxy",
        "preset": {"resolution": "720p", "fps": 24},
    }
    first_render = client.post(
        f"/api/v1/timelines/{timeline['id']}/render", json=render_payload
    )
    second_render = client.post(
        f"/api/v1/timelines/{timeline['id']}/render", json=render_payload
    )
    assert first_render.status_code == 200
    assert second_render.status_code == 200
    assert second_render.json()["id"] == first_render.json()["id"]
    assert first_render.json()["status"] == "queued"

    active_job = db_session.get(RenderJob, first_render.json()["id"])
    active_job.status = "running"
    active_job.progress = 50
    db_session.commit()

    running_render = client.post(
        f"/api/v1/timelines/{timeline['id']}/render", json=render_payload
    )
    assert running_render.status_code == 200
    assert running_render.json()["id"] == first_render.json()["id"]
    assert running_render.json()["status"] == "running"

    active_job.status = "succeeded"
    active_job.progress = 100
    db_session.commit()

    succeeded_render = client.post(
        f"/api/v1/timelines/{timeline['id']}/render", json=render_payload
    )
    assert succeeded_render.status_code == 200
    assert succeeded_render.json()["id"] == first_render.json()["id"]
    assert succeeded_render.json()["status"] == "succeeded"

    active_job.status = "failed"
    active_job.log = {"code": "no_video_clips"}
    db_session.commit()

    retry_render = client.post(
        f"/api/v1/timelines/{timeline['id']}/render",
        json={**render_payload, "force_new_attempt": True},
    )
    assert retry_render.status_code == 200
    assert retry_render.json()["id"] != first_render.json()["id"]
    assert retry_render.json()["status"] == "queued"

    jobs_response = client.get(f"/api/v1/timelines/{timeline['id']}/render-jobs")
    assert jobs_response.status_code == 200
    assert [job["id"] for job in jobs_response.json()["items"]] == [
        retry_render.json()["id"]
    ]


def test_timeline_create_rejects_invalid_spec(client, db_session):
    episode, script = _bootstrap_episode(db_session)
    spec = _timeline_spec(episode, script)
    del spec["tracks"][0]["clips"][0]["clip_id"]

    response = client.post(
        f"/api/v1/episodes/{episode.id}/timelines",
        json={
            "script_id": script.id,
            "title": "Invalid Timeline",
            "spec": spec,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "timeline_spec_field_missing"


def test_timeline_access_is_scoped_to_story_owner(client, db_session):
    episode, script = _bootstrap_episode(db_session)
    create_response = client.post(
        f"/api/v1/episodes/{episode.id}/timelines",
        json={
            "script_id": script.id,
            "title": "Owner Timeline",
            "spec": _timeline_spec(episode, script),
        },
    )
    assert create_response.status_code == 200
    timeline_id = create_response.json()["id"]

    other_user = User(
        username="timeline_other_user",
        email="timeline_other_user@example.com",
        hashed_password="x",
        is_active=True,
        is_approved=True,
        email_verified=True,
    )
    db_session.add(other_user)
    db_session.commit()
    db_session.refresh(other_user)
    app.dependency_overrides[get_current_active_user] = lambda: other_user

    list_response = client.get(f"/api/v1/episodes/{episode.id}/timelines")
    read_response = client.get(f"/api/v1/timelines/{timeline_id}")

    assert list_response.status_code == 404
    assert read_response.status_code == 404
