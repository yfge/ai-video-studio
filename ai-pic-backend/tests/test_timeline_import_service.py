from app.models.script import Episode, Script, Story
from app.services.timeline_import_service import import_audio_timeline_to_timeline_spec
from app.services.timeline_spec_builder import stable_clip_id
from sqlalchemy.orm import Session


def _bootstrap(db: Session) -> tuple[Episode, Script]:
    story = Story(title="Import Story", genre="drama")
    episode = Episode(story=story, episode_number=1, title="Episode 1")
    script = Script(episode=episode, title="Script 1", content="")
    db.add_all([story, episode, script])
    db.commit()
    db.refresh(episode)
    db.refresh(script)
    return episode, script


def _audio_timeline(script: Script, *, version: int = 3) -> dict:
    return {
        "script_id": script.id,
        "episode_audio": {
            "oss_url": "https://cdn.example.com/episode.mp3",
            "duration_seconds": 2.0,
            "version": version,
        },
        "beats": [
            {
                "scene_id": 11,
                "scene_number": 1,
                "beat_id": 101,
                "beat_type": "dialogue",
                "speaker_name": "A",
                "text": "hello",
                "start_ms": 0,
                "end_ms": 1200,
            },
            {
                "scene_id": 11,
                "scene_number": 1,
                "beat_id": 102,
                "beat_type": "pause",
                "text": "",
                "start_ms": 1200,
                "end_ms": 2000,
            },
        ],
    }


def test_import_audio_timeline_creates_timeline_spec_tracks(db_session):
    episode, script = _bootstrap(db_session)

    result = import_audio_timeline_to_timeline_spec(
        db_session,
        episode=episode,
        script=script,
        audio_timeline=_audio_timeline(script),
        user_id=9,
    )

    assert result.action == "created"
    timeline = result.timeline
    assert timeline.version == 1
    assert timeline.source_audio_timeline_version == 3
    assert timeline.created_by == 9

    spec = timeline.spec
    assert spec["spec_version"] == "timeline.v1"
    assert spec["timeline_id"] == timeline.id
    assert spec["fps"] == 24
    assert spec["resolution"] == "1080x1920"
    assert spec["duration_ms"] == 2000
    tracks = {track["track_type"]: track for track in spec["tracks"]}
    assert set(tracks) == {"dialogue", "video", "subtitle"}
    assert len(tracks["dialogue"]["clips"]) == 2
    assert len(tracks["video"]["clips"]) == 2
    assert len(tracks["subtitle"]["clips"]) == 1

    dialogue_clip = tracks["dialogue"]["clips"][0]
    assert dialogue_clip["clip_id"] == stable_clip_id(
        track_type="dialogue", scene_id=11, beat_id=101, ordinal=1
    )
    assert dialogue_clip["clip_id"] == "dialogue_scene_11_beat_101_001"
    assert dialogue_clip["asset_ref"]["url"] == "https://cdn.example.com/episode.mp3"
    assert dialogue_clip["source"] == {
        "kind": "audio_timeline_beat",
        "scene_id": 11,
        "beat_id": 101,
        "audio_timeline_version": 3,
    }
    assert dialogue_clip["source_refs"]["scene_beat_id"] == 101


def test_import_audio_timeline_skips_then_updates_with_stable_clip_ids(db_session):
    episode, script = _bootstrap(db_session)

    created = import_audio_timeline_to_timeline_spec(
        db_session,
        episode=episode,
        script=script,
        audio_timeline=_audio_timeline(script, version=1),
    )
    skipped = import_audio_timeline_to_timeline_spec(
        db_session,
        episode=episode,
        script=script,
        audio_timeline=_audio_timeline(script, version=1),
    )
    updated = import_audio_timeline_to_timeline_spec(
        db_session,
        episode=episode,
        script=script,
        audio_timeline=_audio_timeline(script, version=2),
        overwrite=True,
    )

    first_clip_id = created.timeline.spec["tracks"][0]["clips"][0]["clip_id"]
    updated_clip_id = updated.timeline.spec["tracks"][0]["clips"][0]["clip_id"]

    assert skipped.action == "skipped"
    assert skipped.timeline.id == created.timeline.id
    assert updated.action == "updated"
    assert updated.timeline.version == 2
    assert updated.timeline.source_audio_timeline_version == 2
    assert updated.timeline.spec["timeline_id"] == created.timeline.id
    assert updated_clip_id == first_clip_id
