from app.models.script import Episode, Script, Story
from app.services.timeline_import_service import import_audio_timeline_to_timeline_spec
from sqlalchemy.orm import Session


def _bootstrap(db: Session) -> tuple[Episode, Script]:
    story = Story(title="Timeline Pause Story", genre="drama")
    episode = Episode(story=story, episode_number=1, title="Episode 1")
    script = Script(episode=episode, title="Script 1", content="")
    db.add_all([story, episode, script])
    db.commit()
    db.refresh(episode)
    db.refresh(script)
    return episode, script


def test_import_audio_timeline_absorbs_short_pauses_into_previous_video_clip(
    db_session,
):
    episode, script = _bootstrap(db_session)
    audio_timeline = {
        "script_id": script.id,
        "episode_audio": {
            "oss_url": "https://cdn.example.com/episode.mp3",
            "duration_seconds": 4.7,
            "version": 5,
        },
        "beats": [
            {
                "scene_id": 21,
                "scene_number": 1,
                "beat_id": 201,
                "beat_type": "dialogue",
                "speaker_name": "A",
                "text": "Look at this.",
                "start_ms": 0,
                "end_ms": 1000,
            },
            {
                "scene_id": 21,
                "scene_number": 1,
                "beat_id": 202,
                "beat_type": "pause",
                "text": "",
                "start_ms": 1000,
                "end_ms": 1420,
            },
            {
                "scene_id": 21,
                "scene_number": 1,
                "beat_id": 203,
                "beat_type": "action",
                "text": "Camera settles on the window.",
                "start_ms": 1420,
                "end_ms": 3000,
            },
            {
                "scene_id": 21,
                "scene_number": 1,
                "beat_id": 204,
                "beat_type": "pause",
                "text": "",
                "start_ms": 3000,
                "end_ms": 4700,
            },
        ],
    }

    result = import_audio_timeline_to_timeline_spec(
        db_session,
        episode=episode,
        script=script,
        audio_timeline=audio_timeline,
    )

    tracks = {track["track_type"]: track for track in result.timeline.spec["tracks"]}
    video_clips = tracks["video"]["clips"]
    assert [clip["beat_type"] for clip in video_clips] == [
        "dialogue",
        "action",
        "pause",
    ]
    assert [clip["beat_id"] for clip in video_clips] == [201, 203, 204]
    assert video_clips[0]["end_ms"] == 1420
    assert video_clips[0]["duration_ms"] == 1420
    assert video_clips[0]["absorbed_pause_beat_ids"] == [202]
    assert video_clips[-1]["duration_ms"] == 1700


def test_import_audio_timeline_attaches_short_drama_production_metadata(db_session):
    episode, script = _bootstrap(db_session)
    audio_timeline = {
        "script_id": script.id,
        "episode_audio": {
            "oss_url": "https://cdn.example.com/episode.mp3",
            "duration_seconds": 30,
            "version": 6,
        },
        "beats": [
            {
                "scene_id": 31,
                "scene_number": 1,
                "beat_id": 301,
                "beat_type": "dialogue",
                "speaker_name": "A",
                "text": "你手里的合同是假的。",
                "start_ms": 0,
                "end_ms": 2500,
            },
            {
                "scene_id": 31,
                "scene_number": 1,
                "beat_id": 302,
                "beat_type": "action",
                "text": "她把亲子鉴定拍到桌上。",
                "start_ms": 2500,
                "end_ms": 15000,
            },
            {
                "scene_id": 31,
                "scene_number": 1,
                "beat_id": 303,
                "beat_type": "dialogue",
                "speaker_name": "B",
                "text": "除非你敢打开保险柜。",
                "start_ms": 15000,
                "end_ms": 30000,
            },
        ],
    }

    result = import_audio_timeline_to_timeline_spec(
        db_session,
        episode=episode,
        script=script,
        audio_timeline=audio_timeline,
    )

    spec = result.timeline.spec
    assert spec["production_context"]["format"] == "short_drama"
    assert spec["production_context"]["aspect_ratio"] == "9:16"
    assert spec["production_context"]["business_goal"] == "validate_hook_then_scale"
    assert len(spec["concept_test_pack"]["variants"]) == 3
    quality = spec["short_drama_quality"]
    assert {"hook_score", "conflict_turn_rate", "cliffhanger_score"} <= set(quality)
    video_clip = next(
        track for track in spec["tracks"] if track["track_type"] == "video"
    )["clips"][0]
    refs = video_clip["source_refs"]
    assert refs["vertical_visual_contract"]["aspect_ratio"] == "9:16"
    assert refs["human_review"]["status"] == "pending"
    assert refs["short_drama_quality"]["hook_role"] == "opening_hook"
