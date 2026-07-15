import json

from app.models.timeline import Timeline, TimelineClipAsset
from app.models.user import User
from app.models.video_generation_task import (
    VideoGenerationTask,
    VideoGenerationTaskStatus,
)
from app.services.video.video_task_timeline_rework_updater import (
    apply_timeline_rework_result,
)
from tests.test_timeline_clip_video_rework_api import (
    _append_video_clip,
    _bootstrap_episode,
    _create_timeline,
    _media_asset,
    _timeline_spec,
)


def test_storyboard_video_result_rebases_when_same_sheet_is_still_current(
    client, db_session
):
    user = db_session.query(User).filter(User.username == "test_admin").one()
    episode, script = _bootstrap_episode(db_session)
    clip_id = "video_scene_001_beat_001_001"
    sheet = _storyboard_sheet(db_session, "safe")
    spec = _append_video_clip(
        _timeline_spec(episode, script),
        clip_id=clip_id,
    )
    spec["tracks"][-1]["clips"][0]["clip_storyboard_sheet_asset_ref"] = {
        "kind": "clip_storyboard_sheet",
        "media_asset_id": sheet.id,
    }
    created = _create_timeline(client, episode, script, spec)
    timeline = _bump_timeline_version(db_session, created["id"])
    params = _params(created["id"], created["version"], clip_id, sheet_id=sheet.id)
    task = _video_task(db_session, user.id, params, "provider-rebase-safe")

    apply_timeline_rework_result(
        db_session,
        task,
        {"video_url": "https://example.com/rebased.mp4", "duration": 1.2},
        params,
    )

    link = (
        db_session.query(TimelineClipAsset)
        .filter_by(clip_id=clip_id, asset_role="generated_video")
        .one()
    )
    assert link.timeline_version == timeline.version
    assert link.source_ref["timeline_rebased"] is True
    assert link.source_ref["requested_timeline_version"] == created["version"]
    assert link.source_ref["applied_timeline_version"] == timeline.version


def test_storyboard_video_result_does_not_overwrite_newer_sheet(client, db_session):
    user = db_session.query(User).filter(User.username == "test_admin").one()
    episode, script = _bootstrap_episode(db_session)
    clip_id = "video_scene_001_beat_001_001"
    submitted_sheet = _storyboard_sheet(db_session, "submitted")
    replacement_sheet = _storyboard_sheet(db_session, "replacement")
    spec = _append_video_clip(
        _timeline_spec(episode, script),
        clip_id=clip_id,
    )
    spec["tracks"][-1]["clips"][0]["clip_storyboard_sheet_asset_ref"] = {
        "kind": "clip_storyboard_sheet",
        "media_asset_id": replacement_sheet.id,
    }
    created = _create_timeline(client, episode, script, spec)
    _bump_timeline_version(db_session, created["id"])
    params = _params(
        created["id"],
        created["version"],
        clip_id,
        sheet_id=submitted_sheet.id,
    )
    task = _video_task(db_session, user.id, params, "provider-rebase-stale")

    apply_timeline_rework_result(
        db_session,
        task,
        {"video_url": "https://example.com/stale.mp4", "duration": 1.2},
        params,
    )

    assert not (
        db_session.query(TimelineClipAsset)
        .filter_by(clip_id=clip_id, asset_role="generated_video")
        .count()
    )


def _storyboard_sheet(db_session, suffix):
    return _media_asset(
        db_session,
        asset_type="image",
        origin="clip_storyboard_sheet",
        file_url=f"https://example.com/{suffix}.png",
        mime_type="image/png",
    )


def _bump_timeline_version(db_session, timeline_id):
    timeline = db_session.get(Timeline, timeline_id)
    timeline.version += 1
    timeline.spec = {**timeline.spec, "version": timeline.version}
    db_session.commit()
    db_session.refresh(timeline)
    return timeline


def _params(timeline_id, timeline_version, clip_id, *, sheet_id):
    return {
        "timeline_rework": {
            "timeline_id": timeline_id,
            "timeline_version": timeline_version,
            "clip_id": clip_id,
            "asset_role": "generated_video",
            "auto_render": False,
            "reference_mode": "clip_storyboard_sheet",
            "clip_storyboard": {"sheet_media_asset_id": sheet_id},
        }
    }


def _video_task(db_session, user_id, params, provider_task_id):
    task = VideoGenerationTask(
        user_id=user_id,
        provider="mock-provider",
        provider_task_id=provider_task_id,
        model="mock-video",
        model_type="image_to_video",
        prompt="Animate the storyboard sheet",
        parameters=json.dumps(params),
        status=VideoGenerationTaskStatus.SUCCEEDED,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task
