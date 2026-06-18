from types import SimpleNamespace

from app.models.timeline import Timeline, TimelineRevision
from app.services.timeline_shot_plan_payloads import build_timeline_shot_plan_prompt
from tests.timeline_shot_plan_batch_helpers import (
    _BatchAIManager,
    _clip_ids_from_prompt,
    _create_timeline_with_spec,
    _large_timeline_spec,
)
from tests.timeline_shot_plan_test_helpers import (
    _bootstrap_episode,
    _create_timeline,
    _FakeAIManager,
    _timeline_spec,
    _valid_shots,
)


def test_timeline_shot_plan_api_updates_timeline_with_stable_clip_ids(
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
            "prefer_provider": "deepseek",
            "model": "deepseek-v4-flash",
            "style": "3d_cartoon",
        },
    )

    assert response.status_code == 200
    updated = response.json()
    assert updated["version"] == 2
    tracks = {track["track_type"]: track for track in updated["spec"]["tracks"]}
    video_clip = tracks["video"]["clips"][0]
    shot_plan = video_clip["source_refs"]["timeline_shot_plan"]
    assert video_clip["clip_id"] == "video_scene_001_beat_001_001"
    assert video_clip["duration_ms"] == 4000
    assert shot_plan["clip_id"] == video_clip["clip_id"]
    assert shot_plan["provider"] == "deepseek"
    assert shot_plan["model"] == "deepseek-v4-flash"
    assert shot_plan["style"] == "3d_cartoon"
    assert shot_plan["direction_anchor"] == "朝向孤独清道夫发现线索的冷幽默镜头"
    assert shot_plan["aesthetic_reference"] == (
        "1960s atomic-punk, IMAX film, Panavision C lens"
    )
    assert shot_plan["composition_geometry"] == (
        "subject centered, glowing bead lower third"
    )
    assert shot_plan["motion_timeline"][1]["at_ms"] == 1800
    assert shot_plan["emotional_landing"] == (
        "quiet discovery with lonely hero restraint"
    )
    assert "时间线先走" in fake_ai.calls[0]["prompt"]
    assert fake_ai.calls[0]["prefer_provider"] == "deepseek"
    assert fake_ai.calls[0]["model"] == "deepseek-v4-flash"

    revisions = (
        db_session.query(TimelineRevision)
        .filter(TimelineRevision.timeline_id == timeline["id"])
        .order_by(TimelineRevision.timeline_version)
        .all()
    )
    assert [item.timeline_version for item in revisions] == [1, 2]


def test_timeline_shot_plan_api_rejects_invalid_plan_without_updating(
    client,
    db_session,
    monkeypatch,
):
    fake_ai = _FakeAIManager([{**_valid_shots()[0], "duration_ms": 3000}])
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
    refreshed = db_session.get(Timeline, timeline["id"])
    assert refreshed.version == 1
    video_clip = refreshed.spec["tracks"][1]["clips"][0]
    assert "timeline_shot_plan" not in video_clip["source_refs"]


def test_timeline_shot_plan_prompt_includes_character_anchor_hint():
    episode = SimpleNamespace(id=133)
    script = SimpleNamespace(id=117)
    spec = _timeline_spec(episode, script)
    video_clip = spec["tracks"][1]["clips"][0]
    video_clip["source_refs"]["character_name"] = "小蓝"
    video_clip["source_refs"]["character_appearance_prompt"] = "圆润蓝色机器人"
    video_clip["source_refs"][
        "character_anchor_hint"
    ] = "blue cartoon robot, orange scarf, LED eyes"

    prompt = build_timeline_shot_plan_prompt(spec, style="3d_cartoon")

    assert "character_anchor_hint" in prompt
    assert "blue cartoon robot, orange scarf, LED eyes" in prompt
    assert "same protagonist anchor" in prompt


def test_timeline_shot_plan_api_batches_large_timeline_without_truncation(
    client,
    db_session,
    monkeypatch,
):
    episode, script = _bootstrap_episode(db_session)
    spec = _large_timeline_spec(episode, script, clip_count=52)
    fake_ai = _BatchAIManager(spec)
    monkeypatch.setattr(
        "app.services.timeline_shot_plan_service.ai_service.ai_manager",
        fake_ai,
    )
    timeline = _create_timeline_with_spec(client, episode, script, spec)

    response = client.post(
        f"/api/v1/timelines/{timeline['id']}/shot-plan",
        json={
            "expected_version": timeline["version"],
            "prefer_provider": "deepseek",
            "model": "deepseek-v4-flash",
            "style": "3d_cartoon",
        },
    )

    assert response.status_code == 200
    assert len(fake_ai.calls) == 7
    assert [len(_clip_ids_from_prompt(call["prompt"])) for call in fake_ai.calls] == [
        8,
        8,
        8,
        8,
        8,
        8,
        4,
    ]
    assert [call["max_tokens"] for call in fake_ai.calls] == [
        9600,
        9600,
        9600,
        9600,
        9600,
        9600,
        4800,
    ]
    updated = response.json()
    assert updated["version"] == 2
    tracks = {track["track_type"]: track for track in updated["spec"]["tracks"]}
    shot_refs = [
        clip["source_refs"].get("timeline_shot_plan")
        for clip in tracks["video"]["clips"]
    ]
    assert len(shot_refs) == 52
    assert all(isinstance(ref, dict) for ref in shot_refs)
    assert shot_refs[0]["clip_id"] == "video_clip_001"
    assert shot_refs[-1]["clip_id"] == "video_clip_052"


def test_timeline_shot_plan_api_repairs_invalid_batch_json(
    client,
    db_session,
    monkeypatch,
):
    episode, script = _bootstrap_episode(db_session)
    spec = _large_timeline_spec(episode, script, clip_count=1)
    fake_ai = _BatchAIManager(spec, invalid_attempts=1)
    monkeypatch.setattr(
        "app.services.timeline_shot_plan_service.ai_service.ai_manager",
        fake_ai,
    )
    timeline = _create_timeline_with_spec(client, episode, script, spec)

    response = client.post(
        f"/api/v1/timelines/{timeline['id']}/shot-plan",
        json={"expected_version": timeline["version"]},
    )

    assert response.status_code == 200
    assert len(fake_ai.calls) == 2
    assert fake_ai.calls[0]["max_tokens"] == 4000
    assert fake_ai.calls[1]["max_tokens"] == 4000
    updated = response.json()
    tracks = {track["track_type"]: track for track in updated["spec"]["tracks"]}
    shot_plan = tracks["video"]["clips"][0]["source_refs"]["timeline_shot_plan"]
    assert shot_plan["clip_id"] == "video_clip_001"
