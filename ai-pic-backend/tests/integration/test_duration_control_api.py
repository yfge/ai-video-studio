import json
from typing import Callable

from app.models.script import Episode, Script, Story
from app.models.story_structure import Scene
from app.models.task import Task, TaskStatus, TaskType
from app.models.timeline import Timeline
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


def _create_script_with_scenes(db_session, *, user: User) -> tuple[Script, list[int]]:
    story = Story(
        title="Duration Control Story",
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
    scenes = [
        Scene(
            script=script,
            scene_number="1",
            slug_line="INT. ROOM - DAY",
            summary="Scene 1",
        ),
        Scene(
            script=script,
            scene_number="2",
            slug_line="EXT. STREET - NIGHT",
            summary="Scene 2",
        ),
    ]
    db_session.add_all([story, episode, script, *scenes])
    db_session.commit()
    scene_ids = [scene.id for scene in scenes]
    return script, scene_ids


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


def test_dialogue_audio_generate_async_includes_duration_control(
    client, db_session, monkeypatch
):
    import app.api.v1.endpoints.scripts.dialogue_audio as dialogue_audio_endpoint

    admin_user = db_session.query(User).filter(User.username == "test_admin").first()
    assert admin_user is not None
    script, _ = _create_script_with_scenes(db_session, user=admin_user)

    delay_calls: dict[str, object] = {}

    def _fake_delay(task_id: int, params: dict, user_id: int) -> None:
        delay_calls["task_id"] = task_id
        delay_calls["params"] = params
        delay_calls["user_id"] = user_id

    monkeypatch.setattr(
        dialogue_audio_endpoint.script_dialogue_audio_generate_task,
        "delay",
        _fake_delay,
    )

    payload = {"use_duration_control": True}
    response = client.post(
        f"/api/v1/scripts/{script.id}/dialogue-audio/generate-async", json=payload
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
    assert params["use_duration_control"] is True
    assert delay_calls["params"]["use_duration_control"] is True
    assert delay_calls["user_id"] == admin_user.id


def test_audio_timeline_generate_async_includes_deprecation_headers(
    client, db_session, monkeypatch
):
    import app.api.v1.endpoints.scripts.audio_timeline as audio_timeline_endpoint

    admin_user = db_session.query(User).filter(User.username == "test_admin").first()
    assert admin_user is not None
    script, _ = _create_script_with_scenes(db_session, user=admin_user)

    delay_calls: dict[str, object] = {}

    def _fake_delay(task_id: int, params: dict, user_id: int) -> None:
        delay_calls["task_id"] = task_id
        delay_calls["params"] = params
        delay_calls["user_id"] = user_id

    monkeypatch.setattr(
        audio_timeline_endpoint.script_audio_timeline_generate_task,
        "delay",
        _fake_delay,
    )

    response = client.post(
        f"/api/v1/scripts/{script.id}/audio-timeline/generate-async",
        json={"overwrite": False},
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
    assert params["overwrite"] is False
    assert delay_calls["task_id"] == task_id
    assert delay_calls["user_id"] == admin_user.id


def test_process_audio_timeline_task_imports_timeline_spec(
    db_session, test_db, monkeypatch
):
    import app.api.v1.endpoints.scripts.audio_timeline as audio_timeline_endpoint

    user = _create_user(db_session, username="audio_timeline_admin", is_admin=True)
    script, scene_ids = _create_script_with_scenes(db_session, user=user)
    task = _create_task(db_session, user_id=user.id, title="Audio timeline")

    async def _fake_generate_episode_audio_timeline(
        db_session,  # noqa: ANN001
        *,
        script: Script,
        **_: object,
    ) -> dict:
        return {
            "script_id": script.id,
            "episode_audio": {
                "oss_url": "https://cdn.example.com/episode.mp3",
                "duration_seconds": 2.0,
                "version": 6,
            },
            "beats": [
                {
                    "scene_id": scene_ids[0],
                    "scene_number": 1,
                    "beat_id": 601,
                    "beat_type": "dialogue",
                    "text": "hello",
                    "start_ms": 0,
                    "end_ms": 1000,
                },
                {
                    "scene_id": scene_ids[1],
                    "scene_number": 2,
                    "beat_id": 602,
                    "beat_type": "dialogue",
                    "text": "world",
                    "start_ms": 1000,
                    "end_ms": 2000,
                },
            ],
        }

    monkeypatch.setattr(
        audio_timeline_endpoint,
        "generate_episode_audio_timeline",
        _fake_generate_episode_audio_timeline,
    )
    _patch_session_local(monkeypatch, test_db)

    audio_timeline_endpoint._process_script_audio_timeline_task(
        task.id, {"script_id": script.id, "overwrite": True}, user.id
    )

    session = test_db()
    try:
        refreshed = session.query(Task).filter(Task.id == task.id).first()
        assert refreshed is not None
        assert refreshed.status == TaskStatus.COMPLETED
        timeline = (
            session.query(Timeline)
            .filter(Timeline.episode_id == script.episode_id)
            .filter(Timeline.script_id == script.id)
            .one()
        )
        assert timeline.source_audio_timeline_version == 6
        assert timeline.created_by == user.id
    finally:
        session.close()


def test_process_dialogue_audio_task_uses_duration_control(
    db_session, test_db, monkeypatch
):
    import app.api.v1.endpoints.scripts.dialogue_audio as dialogue_audio_endpoint

    user = _create_user(db_session, username="duration_admin", is_admin=True)
    script, scene_ids = _create_script_with_scenes(db_session, user=user)
    task = _create_task(db_session, user_id=user.id, title="Dialogue audio")

    called: dict[str, object] = {}

    async def _fake_generate_dialogue_with_duration_control(
        db_session,  # noqa: ANN001
        *,
        scenes: list[Scene],
        tts_model: str,
        overwrite_beats: bool,
        progress_callback: Callable[[str], None] | None = None,
        **_: object,
    ) -> dict:
        called["scene_ids"] = [scene.id for scene in scenes]
        called["tts_model"] = tts_model
        called["overwrite_beats"] = overwrite_beats
        if progress_callback:
            progress_callback("mock progress")
        return {"success": True, "statistics": {"duration_ratio": 1.0}}

    monkeypatch.setattr(
        dialogue_audio_endpoint,
        "generate_dialogue_with_duration_control",
        _fake_generate_dialogue_with_duration_control,
    )
    _patch_session_local(monkeypatch, test_db)

    payload = {"script_id": script.id, "use_duration_control": True}
    dialogue_audio_endpoint._process_script_dialogue_audio_task(
        task.id, payload, user.id
    )

    session = test_db()
    try:
        refreshed = session.query(Task).filter(Task.id == task.id).first()
        assert refreshed is not None
        assert refreshed.status == TaskStatus.COMPLETED
        assert refreshed.result_file_path == f"script:{script.id}:dialogue_audio"
    finally:
        session.close()

    assert called["scene_ids"] == scene_ids
    assert called["tts_model"] == "speech-2.6-hd"
    assert called["overwrite_beats"] is True
