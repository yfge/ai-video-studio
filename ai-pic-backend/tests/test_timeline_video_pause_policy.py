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
