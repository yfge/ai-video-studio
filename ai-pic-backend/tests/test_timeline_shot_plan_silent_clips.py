import pytest

from app.models.timeline import Timeline
from tests.test_timeline_shot_plan_api import (
    _FakeAIManager,
    _bootstrap_episode,
    _create_timeline,
    _timeline_spec,
    _valid_shots,
)


def test_timeline_shot_plan_api_allows_silent_pause_clip(
    client,
    db_session,
    monkeypatch,
):
    episode, script = _bootstrap_episode(db_session)
    spec = _timeline_spec(episode, script)
    spec["duration_ms"] = 4300
    spec["tracks"][1]["clips"].append(
        {
            "clip_id": "video_scene_001_beat_pause_002",
            "track_type": "video",
            "scene_id": "scene_001",
            "beat_id": "beat_pause",
            "ordinal": 2,
            "start_ms": 4000,
            "end_ms": 4300,
            "duration_ms": 300,
            "text": None,
            "beat_type": "pause",
            "placeholder": True,
            "asset_ref": None,
            "source": {
                "kind": "audio_timeline_beat",
                "scene_id": "scene_001",
                "beat_id": "beat_pause",
                "audio_timeline_version": 1,
            },
            "source_refs": {
                "scene_beat_id": "beat_pause",
                "audio_timeline_version": 1,
            },
        }
    )
    silent_shot = {
        **_valid_shots()[0],
        "clip_id": "video_scene_001_beat_pause_002",
        "duration_ms": 300,
        "plot": "",
        "dialogue_source": "",
        "visual_prompt": "3D cartoon silent beat, dust settles in the room",
        "video_prompt": (
            "3D cartoon silent pause beat, dust settles in the room, "
            "same blue robot holds still, static camera, no dialogue, duration 300ms"
        ),
        "camera": "static wide shot",
        "action": "dust settles during a brief silent pause",
    }
    fake_ai = _FakeAIManager([*_valid_shots(), silent_shot])
    monkeypatch.setattr(
        "app.services.timeline_shot_plan_service.ai_service.ai_manager",
        fake_ai,
    )
    response = client.post(
        f"/api/v1/episodes/{episode.id}/timelines",
        json={
            "script_id": script.id,
            "title": "Shot Plan Timeline With Pause",
            "spec": spec,
            "source_audio_timeline_version": 1,
        },
    )
    assert response.status_code == 200
    timeline = response.json()

    response = client.post(
        f"/api/v1/timelines/{timeline['id']}/shot-plan",
        json={"expected_version": timeline["version"]},
    )

    assert response.status_code == 200
    assert fake_ai.calls[0]["max_tokens"] >= 4000
    updated = response.json()
    tracks = {track["track_type"]: track for track in updated["spec"]["tracks"]}
    shot_plan = tracks["video"]["clips"][1]["source_refs"]["timeline_shot_plan"]
    assert shot_plan["plot"] == ""
    assert shot_plan["dialogue_source"] == ""


@pytest.mark.parametrize(
    ("field_name", "expected_message"),
    [
        ("plot", "timeline shot plan plot missing"),
        ("dialogue_source", "timeline shot plan dialogue source missing"),
    ],
)
def test_timeline_shot_plan_api_rejects_empty_text_for_sourced_clip(
    client,
    db_session,
    monkeypatch,
    field_name,
    expected_message,
):
    shot = {**_valid_shots()[0], field_name: ""}
    fake_ai = _FakeAIManager([shot])
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
    assert response.json()["detail"]["message"] == expected_message
    refreshed = db_session.get(Timeline, timeline["id"])
    assert refreshed.version == 1
    video_clip = refreshed.spec["tracks"][1]["clips"][0]
    assert "timeline_shot_plan" not in video_clip["source_refs"]


def test_timeline_shot_plan_api_allows_action_clip_without_dialogue_source(
    client,
    db_session,
    monkeypatch,
):
    episode, script = _bootstrap_episode(db_session)
    spec = _timeline_spec(episode, script)
    for track in spec["tracks"]:
        for clip in track["clips"]:
            clip["beat_type"] = "action"
            clip["speaker_name"] = None
            clip["text"] = "机器人检查时间轴上的第一颗光点。"
    shot = {**_valid_shots()[0], "dialogue_source": ""}
    fake_ai = _FakeAIManager([shot])
    monkeypatch.setattr(
        "app.services.timeline_shot_plan_service.ai_service.ai_manager",
        fake_ai,
    )
    response = client.post(
        f"/api/v1/episodes/{episode.id}/timelines",
        json={
            "script_id": script.id,
            "title": "Action Shot Without Dialogue",
            "spec": spec,
            "source_audio_timeline_version": 1,
        },
    )
    assert response.status_code == 200
    timeline = response.json()

    response = client.post(
        f"/api/v1/timelines/{timeline['id']}/shot-plan",
        json={"expected_version": timeline["version"]},
    )

    assert response.status_code == 200
    shot_plan = response.json()["spec"]["tracks"][1]["clips"][0]["source_refs"][
        "timeline_shot_plan"
    ]
    assert shot_plan["dialogue_source"] == ""
