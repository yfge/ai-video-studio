from app.models.timeline import Timeline
from tests.test_timeline_shot_plan_api import (
    _FakeAIManager,
    _bootstrap_episode,
    _create_timeline,
    _valid_shots,
)


def test_timeline_shot_plan_api_accepts_live_action_prompt_layers(
    client,
    db_session,
    monkeypatch,
):
    fake_ai = _FakeAIManager(_valid_shots())
    monkeypatch.setattr(
        "app.services.timeline_shot_plan_service.ai_service.ai_manager",
        fake_ai,
    )
    episode, script = _bootstrap_episode(db_session)
    timeline = _create_timeline(client, episode, script)

    response = client.post(
        f"/api/v1/timelines/{timeline['id']}/shot-plan",
        json={
            "expected_version": timeline["version"],
            "style": "live_action",
        },
    )

    assert response.status_code == 200
    updated = response.json()
    tracks = {track["track_type"]: track for track in updated["spec"]["tracks"]}
    shot_plan = tracks["video"]["clips"][0]["source_refs"]["timeline_shot_plan"]
    assert shot_plan["style"] == "live_action"
    assert "真人电影" in fake_ai.calls[0]["prompt"]
    assert "do not force cartoon" in fake_ai.calls[0]["prompt"]


def test_timeline_shot_plan_api_rejects_motion_timeline_outside_clip_duration(
    client,
    db_session,
    monkeypatch,
):
    bad_shot = {**_valid_shots()[0]}
    bad_shot["motion_timeline"] = [
        {"at_ms": 0, "action": "robot enters"},
        {"at_ms": 4500, "action": "robot points after the clip has ended"},
    ]
    fake_ai = _FakeAIManager([bad_shot])
    monkeypatch.setattr(
        "app.services.timeline_shot_plan_service.ai_service.ai_manager",
        fake_ai,
    )
    episode, script = _bootstrap_episode(db_session)
    timeline = _create_timeline(client, episode, script)

    response = client.post(
        f"/api/v1/timelines/{timeline['id']}/shot-plan",
        json={"expected_version": timeline["version"]},
    )

    assert response.status_code == 502
    assert "motion_timeline" in str(response.json()["detail"]["errors"])
    refreshed = db_session.get(Timeline, timeline["id"])
    assert refreshed.version == 1
