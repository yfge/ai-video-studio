import json

from app.models.script import Episode, Script, Story
from app.models.task import Task, TaskStatus, TaskType
from app.models.user import User


def _patch_session_local(monkeypatch, session_factory) -> None:
    import app.core.database as db_module

    monkeypatch.setattr(db_module, "SessionLocal", session_factory)


def _create_user(db_session, *, username: str, is_admin: bool) -> User:
    user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password="not-used-in-tests",
        is_active=True,
        is_approved=True,
        email_verified=True,
        is_admin=is_admin,
        is_superuser=is_admin,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _create_script(db_session, *, user: User) -> Script:
    story = Story(
        title="Storyboard Audio Story",
        genre="drama",
        theme="timing",
        target_audience="all",
        user_id=user.id,
    )
    episode = Episode(
        title="Episode 1",
        episode_number=1,
        duration_minutes=6,
        story=story,
    )
    script = Script(title="Script 1", content="", episode=episode)
    db_session.add_all([story, episode, script])
    db_session.commit()
    db_session.refresh(script)
    return script


def _create_task(db_session, *, user_id: int, title: str) -> Task:
    task = Task(
        title=title,
        task_type=TaskType.IMAGE_GENERATION,
        status=TaskStatus.PENDING,
        user_id=user_id,
    )
    db_session.add(task)
    db_session.commit()
    return task


def test_storyboard_from_audio_timeline_generate_async_queues_task(
    client, db_session, monkeypatch
):
    import app.api.v1.endpoints.scripts.audio_storyboard as audio_storyboard_endpoint

    admin_user = db_session.query(User).filter(User.username == "test_admin").first()
    assert admin_user is not None
    script = _create_script(db_session, user=admin_user)

    delay_calls: dict[str, object] = {}

    def _fake_delay(task_id: int, params: dict, user_id: int) -> None:
        delay_calls["task_id"] = task_id
        delay_calls["params"] = params
        delay_calls["user_id"] = user_id

    monkeypatch.setattr(
        audio_storyboard_endpoint.script_audio_storyboard_generate_task,
        "delay",
        _fake_delay,
    )

    payload = {"overwrite_existing": True, "min_pause_seconds": 2.5}
    response = client.post(
        f"/api/v1/scripts/{script.id}/storyboard/from-audio-timeline/generate-async",
        json=payload,
    )
    assert response.status_code == 200, response.text
    assert response.headers.get("deprecation") == "true"
    assert response.headers.get("x-api-deprecated") == "Use timeline-pipeline endpoint"
    link = response.headers.get("link", "")
    assert f"/api/v1/scripts/{script.id}/timeline-pipeline/generate-async" in link

    task_id = response.json()["data"]["task_id"]
    task = db_session.query(Task).filter(Task.id == task_id).first()
    assert task is not None

    params = json.loads(task.parameters or "{}")
    assert params["script_id"] == script.id
    assert params["overwrite_existing"] is True
    assert params["min_pause_seconds"] == 2.5
    assert delay_calls["user_id"] == admin_user.id
    assert delay_calls["params"]["script_id"] == script.id


def test_process_storyboard_from_audio_timeline_task(db_session, test_db, monkeypatch):
    import app.api.v1.endpoints.scripts.audio_storyboard as audio_storyboard_endpoint

    user = _create_user(db_session, username="storyboard_admin", is_admin=True)
    script = _create_script(db_session, user=user)
    task = _create_task(db_session, user_id=user.id, title="Audio storyboard")

    called: dict[str, object] = {}

    def _fake_generate_storyboard_from_episode_audio_timeline(
        db_session,  # noqa: ANN001
        *,
        script,
        episode,
        overwrite_existing: bool,
        min_pause_duration_ms: int,
        legacy_support_view: bool,
    ) -> None:
        called["script_id"] = script.id
        called["episode_id"] = episode.id
        called["overwrite_existing"] = overwrite_existing
        called["min_pause_duration_ms"] = min_pause_duration_ms
        called["legacy_support_view"] = legacy_support_view

    monkeypatch.setattr(
        audio_storyboard_endpoint,
        "generate_storyboard_from_episode_audio_timeline",
        _fake_generate_storyboard_from_episode_audio_timeline,
    )
    _patch_session_local(monkeypatch, test_db)

    payload = {
        "script_id": script.id,
        "overwrite_existing": True,
        "min_pause_seconds": 2.25,
    }
    audio_storyboard_endpoint._process_script_audio_storyboard_task(
        task.id,
        payload,
        user.id,
    )

    session = test_db()
    try:
        refreshed = session.query(Task).filter(Task.id == task.id).first()
        assert refreshed is not None
        assert refreshed.status == TaskStatus.COMPLETED
        assert (
            refreshed.result_file_path
            == f"script:{script.id}:storyboard_from_audio_timeline"
        )
    finally:
        session.close()

    assert called["script_id"] == script.id
    assert called["overwrite_existing"] is True
    assert called["min_pause_duration_ms"] == 2250
    assert called["legacy_support_view"] is True
