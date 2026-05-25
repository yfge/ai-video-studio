from app.core.middleware import get_current_active_user
from app.main import app
from app.models.script import Episode, Script, Story
from app.models.timeline import TimelineRevision
from app.models.user import User
from app.services.timeline_service import TimelineService
from sqlalchemy.orm import Session


def _bootstrap_episode(db: Session) -> tuple[Episode, Script]:
    user = db.query(User).filter(User.username == "test_admin").one()
    story = Story(title="Lifecycle Story", genre="short_drama", user_id=user.id)
    episode = Episode(
        story=story,
        episode_number=1,
        title="Lifecycle Pilot",
        duration_minutes=3,
    )
    script = Script(
        episode=episode,
        title="Lifecycle Script",
        content="A: hello",
        scenes=[{"scene_id": "scene_001", "title": "Opening"}],
    )
    db.add_all([story, episode, script])
    db.commit()
    db.refresh(episode)
    db.refresh(script)
    return episode, script


def _timeline_spec(episode: Episode, script: Script, duration_ms: int) -> dict:
    return {
        "spec_version": "timeline.v1",
        "episode_id": episode.id,
        "script_id": script.id,
        "source_audio_timeline_version": 1,
        "tracks": [
            {
                "track_type": "dialogue",
                "clips": [
                    {
                        "clip_id": "dialogue_scene_001_beat_001_001",
                        "scene_id": "scene_001",
                        "beat_id": "beat_001",
                        "start_ms": 0,
                        "duration_ms": duration_ms,
                    }
                ],
            }
        ],
    }


def _create_timeline(client, episode: Episode, script: Script) -> dict:
    response = client.post(
        f"/api/v1/episodes/{episode.id}/timelines",
        json={
            "script_id": script.id,
            "title": "Lifecycle Timeline",
            "spec": _timeline_spec(episode, script, 1200),
            "source_audio_timeline_version": 1,
        },
    )
    assert response.status_code == 200
    return response.json()


def _queue_render(client, timeline_id: int, timeline_version: int) -> dict:
    response = client.post(
        f"/api/v1/timelines/{timeline_id}/render",
        json={
            "timeline_version": timeline_version,
            "render_type": "proxy",
            "preset": {"resolution": "720p", "fps": 24},
        },
    )
    assert response.status_code == 200
    return response.json()


def test_timeline_delete_restore_and_render_job_lifecycle(
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
    timeline = _create_timeline(client, episode, script)
    render_job = _queue_render(client, timeline["id"], timeline["version"])

    stale_delete = client.request(
        "DELETE",
        f"/api/v1/timelines/{timeline['id']}",
        json={"expected_version": timeline["version"] + 1},
    )
    assert stale_delete.status_code == 409

    delete_job = client.request(
        "DELETE",
        f"/api/v1/timelines/{timeline['id']}/render-jobs/{render_job['id']}",
        json={"expected_version": timeline["version"], "reason": "bad_attempt"},
    )
    assert delete_job.status_code == 200
    assert delete_job.json()["is_deleted"] is True

    jobs = client.get(f"/api/v1/timelines/{timeline['id']}/render-jobs")
    assert jobs.status_code == 200
    assert jobs.json()["items"] == []

    restore_job = client.post(
        f"/api/v1/timelines/{timeline['id']}/render-jobs/{render_job['id']}/restore",
        json={"expected_version": timeline["version"]},
    )
    assert restore_job.status_code == 200
    assert restore_job.json()["is_deleted"] is False

    delete_timeline = client.request(
        "DELETE",
        f"/api/v1/timelines/{timeline['id']}",
        json={"expected_version": timeline["version"], "reason": "operator_cleanup"},
    )
    assert delete_timeline.status_code == 200
    assert delete_timeline.json()["is_deleted"] is True
    assert delete_timeline.json()["deleted_reason"] == "operator_cleanup"

    assert client.get(f"/api/v1/timelines/{timeline['id']}").status_code == 404
    list_response = client.get(f"/api/v1/episodes/{episode.id}/timelines")
    assert list_response.json()["items"] == []

    restore_timeline = client.post(
        f"/api/v1/timelines/{timeline['id']}/restore",
        json={"expected_version": timeline["version"]},
    )
    assert restore_timeline.status_code == 200
    assert restore_timeline.json()["is_deleted"] is False
    assert client.get(f"/api/v1/timelines/{timeline['id']}").status_code == 200


def test_timeline_rollback_creates_new_version_and_preserves_render_jobs(
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
    timeline = _create_timeline(client, episode, script)

    update_response = client.patch(
        f"/api/v1/timelines/{timeline['id']}",
        json={
            "expected_version": 1,
            "spec": _timeline_spec(episode, script, 2400),
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    render_job = _queue_render(client, timeline["id"], updated["version"])

    stale_rollback = client.post(
        f"/api/v1/timelines/{timeline['id']}/rollback",
        json={"expected_version": 1, "target_version": 1},
    )
    assert stale_rollback.status_code == 409

    rollback = client.post(
        f"/api/v1/timelines/{timeline['id']}/rollback",
        json={"expected_version": 2, "target_version": 1},
    )
    assert rollback.status_code == 200
    rolled_back = rollback.json()
    assert rolled_back["version"] == 3
    assert rolled_back["rollback"]["source_version"] == 2
    assert rolled_back["rollback"]["target_version"] == 1
    clip = rolled_back["spec"]["tracks"][0]["clips"][0]
    assert clip["duration_ms"] == 1200

    jobs = client.get(f"/api/v1/timelines/{timeline['id']}/render-jobs")
    assert jobs.status_code == 200
    assert jobs.json()["items"][0]["id"] == render_job["id"]
    assert jobs.json()["items"][0]["timeline_version"] == 2

    revisions = (
        db_session.query(TimelineRevision)
        .filter(TimelineRevision.timeline_id == timeline["id"])
        .order_by(TimelineRevision.timeline_version)
        .all()
    )
    assert [item.timeline_version for item in revisions] == [1, 2, 3]


def test_timeline_lifecycle_access_is_scoped_to_story_owner(client, db_session):
    episode, script = _bootstrap_episode(db_session)
    timeline = _create_timeline(client, episode, script)
    other_user = User(
        username="timeline_lifecycle_other",
        email="timeline_lifecycle_other@example.com",
        hashed_password="x",
        is_active=True,
        is_approved=True,
        email_verified=True,
    )
    db_session.add(other_user)
    db_session.commit()
    app.dependency_overrides[get_current_active_user] = lambda: other_user

    delete_response = client.request(
        "DELETE",
        f"/api/v1/timelines/{timeline['id']}",
        json={"expected_version": timeline["version"]},
    )
    rollback_response = client.post(
        f"/api/v1/timelines/{timeline['id']}/rollback",
        json={"expected_version": timeline["version"], "target_version": 1},
    )

    assert delete_response.status_code == 404
    assert rollback_response.status_code == 404
