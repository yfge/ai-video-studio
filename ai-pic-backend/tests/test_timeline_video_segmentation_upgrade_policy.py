from copy import deepcopy

import pytest
from app.models.script import Episode, Script, Story
from app.models.task import Task, TaskType
from app.models.timeline import MediaAsset, RenderJob, TimelineClipAsset
from app.models.user import User
from app.services.timeline_import_service import import_audio_timeline_to_timeline_spec


def test_legacy_timeline_without_video_is_automatically_versioned(db_session):
    episode, script, audio_timeline, timeline = _legacy_timeline(db_session)
    image = _asset(db_session, "image")
    db_session.add(
        TimelineClipAsset(
            timeline_id=timeline.id,
            timeline_version=timeline.version,
            clip_id=_video_clip_id(timeline),
            track_type="video",
            asset_role="storyboard_image",
            media_asset_id=image.id,
        )
    )
    db_session.commit()

    result = import_audio_timeline_to_timeline_spec(
        db_session,
        episode=episode,
        script=script,
        audio_timeline=audio_timeline,
    )

    assert result.action == "updated"
    assert result.timeline.version == 2
    assert result.timeline.spec["source"]["video_segmentation"]["strategy"] == (
        "beat_window_v2"
    )


def test_legacy_segmentation_upgrade_does_not_depend_on_old_audio_version(db_session):
    episode, script, audio_timeline, timeline = _legacy_timeline(db_session)
    timeline.source_audio_timeline_version = 0
    db_session.commit()

    result = import_audio_timeline_to_timeline_spec(
        db_session,
        episode=episode,
        script=script,
        audio_timeline=audio_timeline,
    )

    assert result.action == "updated"
    assert result.timeline.version == 2
    assert result.timeline.source_audio_timeline_version == 1


@pytest.mark.parametrize("protection", ["video", "active_task", "render"])
def test_legacy_timeline_with_production_state_is_not_automatically_resegmented(
    db_session,
    protection,
):
    episode, script, audio_timeline, timeline = _legacy_timeline(db_session)
    if protection == "video":
        video = _asset(db_session, "video")
        db_session.add(
            TimelineClipAsset(
                timeline_id=timeline.id,
                timeline_version=timeline.version,
                clip_id=_video_clip_id(timeline),
                track_type="video",
                asset_role="generated_video",
                media_asset_id=video.id,
            )
        )
    elif protection == "active_task":
        user = User(
            username="segmentation_worker",
            email="segmentation_worker@example.com",
            hashed_password="test",
            is_active=True,
            is_approved=True,
            email_verified=True,
        )
        db_session.add(user)
        db_session.flush()
        db_session.add(
            Task(
                target_business_id=timeline.business_id,
                title="Active Timeline video",
                task_type=TaskType.VIDEO_GENERATION,
                user_id=user.id,
            )
        )
    else:
        db_session.add(
            RenderJob(
                timeline_id=timeline.id,
                timeline_version=timeline.version,
                render_type="final",
                preset_hash="upgrade-policy",
                preset={"fps": 24},
                status="succeeded",
            )
        )
    db_session.commit()

    result = import_audio_timeline_to_timeline_spec(
        db_session,
        episode=episode,
        script=script,
        audio_timeline=audio_timeline,
    )

    assert result.action == "skipped"
    assert result.timeline.version == 1
    assert "video_segmentation" not in result.timeline.spec["source"]


def _legacy_timeline(db_session):
    story = Story(title="Upgrade Policy", genre="drama")
    episode = Episode(story=story, episode_number=1, title="Episode")
    script = Script(episode=episode, title="Script", content="")
    db_session.add_all([story, episode, script])
    db_session.commit()
    audio_timeline = {
        "script_id": script.id,
        "episode_audio": {"duration_seconds": 6, "version": 1},
        "beats": [
            {
                "scene_id": 1,
                "beat_id": 1,
                "beat_type": "action",
                "text": "A six second shot",
                "start_ms": 0,
                "end_ms": 6000,
            }
        ],
    }
    created = import_audio_timeline_to_timeline_spec(
        db_session,
        episode=episode,
        script=script,
        audio_timeline=audio_timeline,
    )
    spec = deepcopy(created.timeline.spec)
    spec["source"].pop("video_segmentation")
    created.timeline.spec = spec
    db_session.add(created.timeline)
    db_session.commit()
    return episode, script, audio_timeline, created.timeline


def _asset(db_session, asset_type: str) -> MediaAsset:
    asset = MediaAsset(
        asset_type=asset_type,
        origin="provider",
        file_url=f"https://cdn.example.com/{asset_type}",
    )
    db_session.add(asset)
    db_session.commit()
    return asset


def _video_clip_id(timeline) -> str:
    return next(
        track for track in timeline.spec["tracks"] if track["track_type"] == "video"
    )["clips"][0]["clip_id"]
