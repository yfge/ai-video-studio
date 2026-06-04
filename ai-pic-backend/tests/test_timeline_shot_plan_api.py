import json
from types import SimpleNamespace

from app.models.script import Episode, Script, Story
from app.models.timeline import Timeline, TimelineRevision
from app.models.user import User
from app.services.timeline_shot_plan_payloads import build_timeline_shot_plan_prompt
from sqlalchemy.orm import Session


class _FakeAIManager:
    def __init__(self, shots: list[dict]):
        self.shots = shots
        self.calls: list[dict] = []

    async def generate_text(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            success=True,
            data=json.dumps({"shots": self.shots}, ensure_ascii=False),
            provider="deepseek",
            model="deepseek-v4-flash",
            usage={"total_tokens": 123},
            error=None,
        )


def _bootstrap_episode(db: Session) -> tuple[Episode, Script]:
    user = db.query(User).filter(User.username == "test_admin").one()
    story = Story(title="Shot Plan Story", genre="short_drama", user_id=user.id)
    episode = Episode(
        story=story,
        episode_number=1,
        title="Shot Plan Pilot",
        duration_minutes=3,
    )
    script = Script(
        episode=episode,
        title="Shot Plan Script",
        content="机器人: 时间线先走。",
        scenes=[{"scene_id": "scene_001", "title": "Opening"}],
    )
    db.add_all([story, episode, script])
    db.commit()
    db.refresh(episode)
    db.refresh(script)
    return episode, script


def _timeline_spec(episode: Episode, script: Script) -> dict:
    return {
        "spec_version": "timeline.v1",
        "episode_id": episode.id,
        "script_id": script.id,
        "version": 1,
        "source_audio_timeline_version": 1,
        "fps": 24,
        "resolution": "1080x1920",
        "duration_ms": 4000,
        "source": {"type": "api_test"},
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
                        "end_ms": 4000,
                        "duration_ms": 4000,
                        "text": "机器人: 时间线先走。",
                        "speaker_name": "机器人",
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
            },
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
                        "end_ms": 4000,
                        "duration_ms": 4000,
                        "text": "机器人检查时间轴上的第一颗光点。",
                        "placeholder": True,
                        "asset_ref": None,
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
            },
            {
                "track_type": "subtitle",
                "clips": [
                    {
                        "clip_id": "subtitle_scene_001_beat_001_001",
                        "track_type": "subtitle",
                        "scene_id": "scene_001",
                        "beat_id": "beat_001",
                        "ordinal": 1,
                        "start_ms": 0,
                        "end_ms": 4000,
                        "duration_ms": 4000,
                        "text": "机器人: 时间线先走。",
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
            },
        ],
    }


def _create_timeline(client, episode: Episode, script: Script) -> dict:
    response = client.post(
        f"/api/v1/episodes/{episode.id}/timelines",
        json={
            "script_id": script.id,
            "title": "Shot Plan Timeline",
            "spec": _timeline_spec(episode, script),
            "source_audio_timeline_version": 1,
        },
    )
    assert response.status_code == 200
    return response.json()


def _valid_shots() -> list[dict]:
    return [
        {
            "clip_id": "video_scene_001_beat_001_001",
            "duration_ms": 4000,
            "plot": "机器人检查时间轴上的第一颗光点。",
            "dialogue_source": "机器人: 时间线先走。",
            "visual_prompt": "3D cartoon robot points at a glowing timeline bead",
            "video_prompt": (
                "3D cartoon robot points at a glowing timeline bead, dialogue: "
                "机器人: 时间线先走。, clear camera push-in, 4 seconds"
            ),
            "character_anchor": "non-real blue robot with LED eyes",
            "camera": "slow push-in",
            "action": "points at the first glowing timeline bead",
            "direction_anchor": "朝向孤独清道夫发现线索的冷幽默镜头",
            "aesthetic_reference": "1960s atomic-punk, IMAX film, Panavision C lens",
            "shot_type": "low angle medium close-up",
            "camera_movement": "slow push-in",
            "composition_geometry": "subject centered, glowing bead lower third",
            "motion_timeline": [
                {"at_ms": 0, "action": "robot leans into frame"},
                {"at_ms": 1800, "action": "finger points at the bead"},
                {"at_ms": 4000, "action": "LED eyes brighten"},
            ],
            "emotional_landing": "quiet discovery with lonely hero restraint",
            "prompt_method": "direction_reference_geometry_timeline_emotion_v1",
        }
    ]


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
