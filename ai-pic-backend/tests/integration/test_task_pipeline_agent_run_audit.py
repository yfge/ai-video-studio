import json

from app.models.script import Episode, Script, Story
from app.models.task import Task, TaskStatus, TaskType
from app.models.user import User
from app.models.virtual_ip import VirtualIP


def _patch_session_local(monkeypatch, session_factory) -> None:
    import app.core.database as db_module

    monkeypatch.setattr(db_module, "SessionLocal", session_factory)


def _load_task_parameters(task: Task) -> dict:
    raw = task.parameters or "{}"
    parsed = json.loads(raw) if isinstance(raw, str) else {}
    return parsed if isinstance(parsed, dict) else {}


def test_story_episode_script_generate_async_persists_task_agent_run(
    client, db_session, test_db, mock_ai_service, monkeypatch
):
    from app.services import task_worker as task_worker_module

    admin_user = db_session.query(User).filter(User.username == "test_admin").first()
    assert admin_user is not None

    vip = VirtualIP(
        user_id=admin_user.id,
        name="Test VIP",
        description="Test character for story generation",
        is_active=True,
        is_public=False,
    )
    db_session.add(vip)
    db_session.commit()
    db_session.refresh(vip)

    _patch_session_local(monkeypatch, test_db)

    delay_calls: dict[str, tuple[int, dict, int]] = {}

    def _capture_story_delay(task_id: int, request_dict: dict, user_id: int) -> None:
        delay_calls["story"] = (task_id, request_dict, user_id)

    def _capture_episode_delay(task_id: int, request_dict: dict, user_id: int) -> None:
        delay_calls["episode"] = (task_id, request_dict, user_id)

    def _capture_script_delay(task_id: int, request_dict: dict, user_id: int) -> None:
        delay_calls["script"] = (task_id, request_dict, user_id)

    monkeypatch.setattr(
        task_worker_module.story_generate_task, "delay", _capture_story_delay
    )
    monkeypatch.setattr(
        task_worker_module.episode_generate_task, "delay", _capture_episode_delay
    )
    monkeypatch.setattr(
        task_worker_module.script_generate_task, "delay", _capture_script_delay
    )

    story_resp = client.post(
        "/api/v1/stories/generate-async",
        json={"title": "Test Story", "genre": "drama", "character_ids": [vip.id]},
    )
    assert story_resp.status_code == 200, story_resp.text
    story_task_id = story_resp.json()["data"]["task_id"]

    assert delay_calls.get("story", (None, None, None))[0] == story_task_id
    story_task_id, story_payload, story_user_id = delay_calls["story"]
    task_worker_module.story_generate_task.run(story_task_id, story_payload, story_user_id)

    session = test_db()
    try:
        story_task = session.query(Task).filter(Task.id == story_task_id).first()
        assert story_task is not None
        assert story_task.task_type == TaskType.STORY_GENERATION
        assert story_task.status == TaskStatus.COMPLETED, story_task.error_message
        story_params = _load_task_parameters(story_task)
        agent_run = story_params.get("agent_run")
        assert isinstance(agent_run, dict)
        story_id = (agent_run.get("result_ref") or {}).get("story_id")
        assert isinstance(story_id, int)

        story = session.query(Story).filter(Story.id == story_id).first()
        assert story is not None
        assert story.user_id == admin_user.id
        assert isinstance((story.extra_metadata or {}).get("agent_run"), dict)
    finally:
        session.close()

    episodes_resp = client.post(
        "/api/v1/episodes/generate-async",
        json={"story_id": story_id, "episode_count": 1, "episode_duration": 6},
    )
    assert episodes_resp.status_code == 200, episodes_resp.text
    episode_task_id = episodes_resp.json()["data"]["task_id"]

    assert delay_calls.get("episode", (None, None, None))[0] == episode_task_id
    episode_task_id, episode_payload, episode_user_id = delay_calls["episode"]
    task_worker_module.episode_generate_task.run(
        episode_task_id, episode_payload, episode_user_id
    )

    session = test_db()
    try:
        episode_task = session.query(Task).filter(Task.id == episode_task_id).first()
        assert episode_task is not None
        assert episode_task.task_type == TaskType.EPISODE_GENERATION
        assert episode_task.status == TaskStatus.COMPLETED, episode_task.error_message
        episode_params = _load_task_parameters(episode_task)
        ep_agent_run = episode_params.get("agent_run")
        assert isinstance(ep_agent_run, dict)
        result_ref = ep_agent_run.get("result_ref") or {}
        assert result_ref.get("story_id") == story_id
        episode_ids = result_ref.get("episode_ids") or []
        assert isinstance(episode_ids, list) and episode_ids
        episode_id = episode_ids[0]
        assert isinstance(episode_id, int)

        episode = session.query(Episode).filter(Episode.id == episode_id).first()
        assert episode is not None
        assert episode.story_id == story_id
        assert isinstance((episode.extra_metadata or {}).get("agent_run"), dict)
    finally:
        session.close()

    script_resp = client.post(
        "/api/v1/scripts/generate-async",
        json={
            "episode_id": episode_id,
            "market_region": "SEA",
            "micro_genre": "test",
        },
    )
    assert script_resp.status_code == 200, script_resp.text
    script_task_id = script_resp.json()["data"]["task_id"]

    assert delay_calls.get("script", (None, None, None))[0] == script_task_id
    script_task_id, script_payload, script_user_id = delay_calls["script"]
    task_worker_module.script_generate_task.run(script_task_id, script_payload, script_user_id)

    session = test_db()
    try:
        script_task = session.query(Task).filter(Task.id == script_task_id).first()
        assert script_task is not None
        assert script_task.task_type == TaskType.SCRIPT_GENERATION
        assert script_task.status == TaskStatus.COMPLETED, script_task.error_message
        script_params = _load_task_parameters(script_task)
        script_agent_run = script_params.get("agent_run")
        assert isinstance(script_agent_run, dict)
        scoring = script_agent_run.get("scoring")
        assert isinstance(scoring, dict)
        assert "script_score" in scoring
        assert "traffic_sheet" in scoring
        assert "asset_tags" in scoring
        script_id = (script_agent_run.get("result_ref") or {}).get("script_id")
        assert isinstance(script_id, int)

        script = session.query(Script).filter(Script.id == script_id).first()
        assert script is not None
        assert script.episode_id == episode_id
        assert isinstance((script.extra_metadata or {}).get("agent_run"), dict)
    finally:
        session.close()
