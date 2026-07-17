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


def test_import_audio_timeline_groups_short_beats_into_one_scene_video_window(
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
    assert len(video_clips) == 1
    assert video_clips[0]["start_ms"] == 0
    assert video_clips[0]["end_ms"] == 4700
    assert video_clips[0]["duration_ms"] == 4700
    assert video_clips[0]["grouped_beat_ids"] == [201, 202, 203, 204]
    assert len(video_clips[0]["source_clip_ids"]) == 4
    assert [clip["beat_id"] for clip in tracks["dialogue"]["clips"]] == [201]
    assert [clip["beat_id"] for clip in tracks["subtitle"]["clips"]] == [201]
    assert result.timeline.spec["source"]["video_segmentation"] == {
        "strategy": "beat_window_v2",
        "min_duration_ms": 5000,
        "target_duration_ms": 6000,
        "max_duration_ms": 8000,
        "tail_min_duration_ms": 3000,
    }


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


def test_video_windows_compact_tiny_beats_and_split_long_beat_without_audio_drift(
    db_session,
):
    episode, script = _bootstrap(db_session)
    beats = [
        _beat(41, 401, "action", 0, 31, "tap"),
        _beat(41, 402, "dialogue", 31, 293, "A", speaker="Lead"),
        _beat(41, 403, "action", 293, 960, "turn"),
        _beat(41, 404, "action", 960, 6000, "cross the room"),
        _beat(41, 405, "dialogue", 6000, 11000, "B", speaker="Guest"),
        _beat(41, 406, "action", 11000, 16000, "door closes"),
        _beat(42, 407, "action", 16000, 25000, "continuous long move"),
    ]
    audio_timeline = {
        "script_id": script.id,
        "episode_audio": {"duration_seconds": 25, "version": 7},
        "beats": beats,
    }

    result = import_audio_timeline_to_timeline_spec(
        db_session,
        episode=episode,
        script=script,
        audio_timeline=audio_timeline,
    )

    tracks = {track["track_type"]: track for track in result.timeline.spec["tracks"]}
    video = tracks["video"]["clips"]
    assert [(clip["start_ms"], clip["end_ms"]) for clip in video] == [
        (0, 6000),
        (6000, 11000),
        (11000, 16000),
        (16000, 22000),
        (22000, 25000),
    ]
    assert video[-1]["clip_id"].endswith("_part_2")
    assert all(5000 <= clip["duration_ms"] <= 8000 for clip in video[:-1])
    assert video[-1]["duration_ms"] == 3000
    assert [clip["start_ms"] for clip in video[1:]] == [
        clip["end_ms"] for clip in video[:-1]
    ]
    assert video[0]["grouped_beat_ids"] == [401, 402, 403, 404]
    assert [clip["beat_id"] for clip in tracks["dialogue"]["clips"]] == [402, 405]
    assert [clip["start_ms"] for clip in tracks["subtitle"]["clips"]] == [31, 6000]
    assert [clip["end_ms"] for clip in tracks["subtitle"]["clips"]] == [293, 11000]


def _beat(
    scene_id: int,
    beat_id: int,
    beat_type: str,
    start_ms: int,
    end_ms: int,
    text: str,
    *,
    speaker: str | None = None,
) -> dict:
    return {
        "scene_id": scene_id,
        "scene_number": scene_id - 40,
        "beat_id": beat_id,
        "beat_type": beat_type,
        "speaker_name": speaker,
        "text": text,
        "start_ms": start_ms,
        "end_ms": end_ms,
    }
