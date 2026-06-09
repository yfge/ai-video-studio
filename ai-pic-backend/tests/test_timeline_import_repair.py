from copy import deepcopy

from app.models.script import Episode, Script, Story
from app.models.timeline import TimelineClipAsset
from app.services.timeline_import_service import import_audio_timeline_to_timeline_spec
from app.services.timeline_spec_builder import stable_clip_id
from sqlalchemy.orm import Session


def _bootstrap(db: Session) -> tuple[Episode, Script]:
    story = Story(title="Timeline Repair Story", genre="drama")
    episode = Episode(story=story, episode_number=1, title="Episode 1")
    script = Script(episode=episode, title="Script 1", content="")
    db.add_all([story, episode, script])
    db.commit()
    db.refresh(episode)
    db.refresh(script)
    return episode, script


def _audio_timeline(script: Script) -> dict:
    return {
        "script_id": script.id,
        "episode_audio": {
            "oss_url": "https://cdn.example.com/episode.mp3",
            "duration_seconds": 1.6,
            "version": 4,
        },
        "beats": [
            {
                "scene_id": 11,
                "scene_number": 1,
                "beat_id": 101,
                "beat_type": "dialogue",
                "text": "hello",
                "start_ms": 0,
                "end_ms": 1200,
            },
            {
                "scene_id": 11,
                "scene_number": 1,
                "beat_id": 102,
                "beat_type": "action",
                "text": "Camera pans",
                "start_ms": 1200,
                "end_ms": 1600,
            },
        ],
    }


def test_import_repairs_non_dialogue_clips_on_audio_tracks(db_session):
    episode, script = _bootstrap(db_session)
    audio_timeline = _audio_timeline(script)
    created = import_audio_timeline_to_timeline_spec(
        db_session,
        episode=episode,
        script=script,
        audio_timeline=audio_timeline,
    )

    spec = deepcopy(created.timeline.spec)
    tracks = {track["track_type"]: track for track in spec["tracks"]}
    action_video_clip = next(
        clip for clip in tracks["video"]["clips"] if clip["beat_type"] == "action"
    )
    tracks["dialogue"]["clips"].append(
        _stale_clip(action_video_clip, track_type="dialogue", with_audio=True)
    )
    tracks["subtitle"]["clips"].append(
        _stale_clip(action_video_clip, track_type="subtitle", with_audio=False)
    )
    created.timeline.spec = spec
    db_session.add(created.timeline)
    db_session.commit()

    repaired = import_audio_timeline_to_timeline_spec(
        db_session,
        episode=episode,
        script=script,
        audio_timeline=audio_timeline,
        overwrite=False,
    )

    assert repaired.action == "updated"
    assert repaired.timeline.version == 2
    repaired_tracks = {
        track["track_type"]: track for track in repaired.timeline.spec["tracks"]
    }
    assert _beat_types(repaired_tracks["dialogue"]) == ["dialogue"]
    assert _beat_types(repaired_tracks["subtitle"]) == ["dialogue"]
    assert _beat_types(repaired_tracks["video"]) == ["dialogue", "action"]
    clip_assets = (
        db_session.query(TimelineClipAsset)
        .filter(TimelineClipAsset.timeline_id == repaired.timeline.id)
        .filter(TimelineClipAsset.timeline_version == 2)
        .filter(TimelineClipAsset.asset_role == "source_audio")
        .all()
    )
    assert [item.clip_id for item in clip_assets] == [
        repaired_tracks["dialogue"]["clips"][0]["clip_id"]
    ]


def test_import_repairs_fallback_narrator_prose_on_audio_tracks(db_session):
    episode, script = _bootstrap(db_session)
    audio_timeline = _audio_timeline(script)
    audio_timeline["beats"].append(
        {
            "scene_id": 12,
            "scene_number": 2,
            "beat_id": 103,
            "beat_type": "dialogue",
            "speaker_name": "旁白",
            "text": "冲突升级：女主整理资料。她对着镜子说：‘我必须进去。’",
            "start_ms": 1600,
            "end_ms": 2200,
        }
    )
    created = import_audio_timeline_to_timeline_spec(
        db_session,
        episode=episode,
        script=script,
        audio_timeline=audio_timeline,
    )

    spec = deepcopy(created.timeline.spec)
    tracks = {track["track_type"]: track for track in spec["tracks"]}
    stale_dialogue_clip = {
        **tracks["video"]["clips"][-1],
        "clip_id": "dialogue_scene_12_beat_103_003",
        "track_type": "dialogue",
        "beat_type": "dialogue",
        "speaker_name": "旁白",
        "asset_ref": {
            "kind": "episode_audio",
            "url": "https://cdn.example.com/episode.mp3",
            "start_ms": 1600,
            "duration_ms": 600,
        },
    }
    tracks["dialogue"]["clips"].append(stale_dialogue_clip)
    created.timeline.spec = spec
    db_session.add(created.timeline)
    db_session.commit()

    repaired = import_audio_timeline_to_timeline_spec(
        db_session,
        episode=episode,
        script=script,
        audio_timeline=audio_timeline,
        overwrite=False,
    )

    assert repaired.action == "updated"
    assert repaired.timeline.version == 2
    repaired_tracks = {
        track["track_type"]: track for track in repaired.timeline.spec["tracks"]
    }
    assert _beat_types(repaired_tracks["dialogue"]) == ["dialogue"]
    assert _beat_types(repaired_tracks["video"]) == ["dialogue", "action", "action"]
    assert repaired_tracks["video"]["clips"][-1]["audio_excluded_reason"] == (
        "fallback_narration"
    )


def _stale_clip(clip: dict, *, track_type: str, with_audio: bool) -> dict:
    stale = {
        **clip,
        "clip_id": stable_clip_id(
            track_type=track_type,
            scene_id=clip["scene_id"],
            beat_id=clip["beat_id"],
            ordinal=clip["ordinal"],
        ),
        "track_type": track_type,
        "asset_ref": None,
    }
    if with_audio:
        stale["asset_ref"] = {
            "kind": "episode_audio",
            "url": "https://cdn.example.com/episode.mp3",
            "start_ms": clip["start_ms"],
            "duration_ms": clip["duration_ms"],
        }
    return stale


def _beat_types(track: dict) -> list[str]:
    return [clip["beat_type"] for clip in track["clips"]]
