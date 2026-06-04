import pytest
from app.models.script import Episode, Script, Story
from app.models.timeline import MediaAsset, TimelineClipAsset, TimelineRevision
from app.services.timeline_import_service import import_audio_timeline_to_timeline_spec
from app.services.timeline_spec_builder import stable_clip_id
from app.services.timeline_spec_validation_types import TimelineSpecValidationError
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
                "beat_type": "action",
                "text": "Camera pans across the control room",
                "start_ms": 1200,
                "end_ms": 1600,
            },
            {
                "scene_id": 11,
                "scene_number": 1,
                "beat_id": 103,
                "beat_type": "pause",
                "text": "",
                "start_ms": 1600,
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
    assert len(tracks["dialogue"]["clips"]) == 1
    assert len(tracks["video"]["clips"]) == 3
    assert len(tracks["subtitle"]["clips"]) == 1
    assert all(
        clip["beat_type"] == "dialogue" for clip in tracks["dialogue"]["clips"]
    )
    assert all(
        clip["beat_type"] == "dialogue" for clip in tracks["subtitle"]["clips"]
    )
    assert [clip["beat_type"] for clip in tracks["video"]["clips"]] == [
        "dialogue",
        "action",
        "pause",
    ]

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
    video_clip = tracks["video"]["clips"][0]
    subtitle_clip = tracks["subtitle"]["clips"][0]
    assert video_clip["clip_id"] == stable_clip_id(
        track_type="video", scene_id=11, beat_id=101, ordinal=1
    )
    assert subtitle_clip["clip_id"] == stable_clip_id(
        track_type="subtitle", scene_id=11, beat_id=101, ordinal=1
    )
    for clip in (dialogue_clip, video_clip, subtitle_clip):
        assert clip["source"]["kind"] == "audio_timeline_beat"
        assert clip["source"]["beat_id"] == 101
        assert clip["source_refs"]["scene_beat_id"] == 101
    revision = db_session.query(TimelineRevision).one()
    assert revision.timeline_id == timeline.id
    assert revision.timeline_version == 1
    assert revision.reason == "imported"
    audio_asset = (
        db_session.query(MediaAsset)
        .filter(MediaAsset.asset_type == "audio", MediaAsset.origin == "imported")
        .one()
    )
    clip_assets = (
        db_session.query(TimelineClipAsset)
        .filter(TimelineClipAsset.asset_role == "source_audio")
        .order_by(TimelineClipAsset.clip_id)
        .all()
    )
    assert [link.media_asset_id for link in clip_assets] == [
        audio_asset.id,
    ]
    assert dialogue_clip["clip_id"] in {link.clip_id for link in clip_assets}


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
    revisions = (
        db_session.query(TimelineRevision)
        .filter(TimelineRevision.timeline_id == created.timeline.id)
        .order_by(TimelineRevision.timeline_version)
        .all()
    )
    assert [item.timeline_version for item in revisions] == [1, 2]


def test_import_falls_back_to_legacy_storyboard_video_timeline(db_session):
    episode, script = _bootstrap(db_session)
    script.extra_metadata = {
        "storyboard": {
            "frames": [
                {
                    "frame_id": "legacy-frame-1",
                    "frame_number": 1,
                    "scene_number": 1,
                    "start_ms": 0,
                    "end_ms": 1000,
                    "video_url": "https://cdn.example.com/legacy-1.mp4",
                },
                {
                    "frame_id": "legacy-frame-2",
                    "frame_number": 2,
                    "scene_number": 1,
                    "start_ms": 1000,
                    "end_ms": 2000,
                    "video_urls": ["https://cdn.example.com/legacy-2.mp4"],
                },
            ]
        }
    }
    audio_timeline = _audio_timeline(script)
    audio_timeline["beats"][1]["start_ms"] = 500

    result = import_audio_timeline_to_timeline_spec(
        db_session,
        episode=episode,
        script=script,
        audio_timeline=audio_timeline,
    )

    assert result.action == "created"
    spec = result.timeline.spec
    assert spec["source"]["type"] == "legacy_storyboard"
    tracks = {track["track_type"]: track for track in spec["tracks"]}
    assert set(tracks) == {"video"}
    clips = tracks["video"]["clips"]
    assert len(clips) == 2
    assert clips[0]["source"]["kind"] == "legacy_storyboard_frame"
    assert clips[0]["video_url"] == "https://cdn.example.com/legacy-1.mp4"
    assert clips[0]["asset_ref"]["url"] == "https://cdn.example.com/legacy-1.mp4"
    assert clips[1]["video_url"] == "https://cdn.example.com/legacy-2.mp4"
    links = (
        db_session.query(TimelineClipAsset)
        .filter(TimelineClipAsset.timeline_id == result.timeline.id)
        .order_by(TimelineClipAsset.clip_id)
        .all()
    )
    assert [link.asset_role for link in links] == [
        "storyboard_video",
        "storyboard_video",
    ]
    assert {link.media_asset.asset_type for link in links} == {"video"}


def test_import_rejects_audio_timeline_without_source_version(db_session):
    episode, script = _bootstrap(db_session)
    audio_timeline = _audio_timeline(script)
    del audio_timeline["episode_audio"]["version"]

    with pytest.raises(TimelineSpecValidationError) as exc:
        import_audio_timeline_to_timeline_spec(
            db_session,
            episode=episode,
            script=script,
            audio_timeline=audio_timeline,
        )

    assert exc.value.code == "timeline_spec_field_invalid"
