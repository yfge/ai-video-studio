from uuid import uuid4

import pytest
from app.models.script import Episode, Script, Story
from app.models.timeline import MediaAsset, RenderJob, Timeline, TimelineClipAsset
from app.models.user import User
from app.services.render.timeline_render_service import TimelineRenderService


def _bootstrap_timeline(db_session, *, spec: dict, storyboard_frames=None):
    user = User(
        username=f"timeline_render_user_{uuid4().hex[:8]}",
        email=f"timeline-render-{uuid4().hex[:8]}@example.com",
        hashed_password="x",
        is_active=True,
        is_admin=True,
    )
    story = Story(title="Render Story", genre="short_drama", user_id=user.id)
    episode = Episode(
        story=story,
        episode_number=1,
        title="Render Episode",
        duration_minutes=3,
    )
    script = Script(
        episode=episode,
        title="Render Script",
        content="A: hello",
        extra_metadata={"storyboard": {"frames": storyboard_frames or []}},
    )
    timeline = Timeline(
        episode=episode,
        script=script,
        episode_business_id=episode.business_id,
        script_business_id=script.business_id,
        title="Main Timeline",
        status="ready",
        spec=spec,
        version=1,
        created_by=user.id,
        updated_by=user.id,
    )
    job = RenderJob(
        timeline=timeline,
        timeline_version=1,
        render_type="proxy",
        preset_hash="hash",
        preset={"resolution": "720p", "fps": 24},
        status="queued",
        progress=0,
        created_by=user.id,
    )
    db_session.add_all([user, story, episode, script, timeline, job])
    db_session.commit()
    db_session.refresh(timeline)
    db_session.refresh(job)
    return user, timeline, job


def _spec_with_video_clip(clip: dict) -> dict:
    return {
        "spec_version": "timeline.v1",
        "episode_id": 1,
        "script_id": 1,
        "version": 1,
        "tracks": [
            {
                "track_type": "video",
                "clips": [clip],
            }
        ],
    }


@pytest.mark.asyncio
async def test_timeline_render_success_creates_media_asset(
    db_session,
    tmp_path,
    monkeypatch,
):
    output_path = tmp_path / "render.mp4"

    async def fake_render_to_temp_file(_clips):
        output_path.write_bytes(b"rendered video")
        return str(output_path)

    monkeypatch.setattr(
        "app.services.render.timeline_render_output.settings.UPLOAD_DIR",
        str(tmp_path / "uploads"),
    )

    asset = MediaAsset(
        asset_type="video",
        origin="ai_generated",
        file_url="https://example.com/clip.mp4",
        mime_type="video/mp4",
    )
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)

    user, _timeline, job = _bootstrap_timeline(
        db_session,
        spec=_spec_with_video_clip(
            {
                "clip_id": "video_scene_1_beat_1_001",
                "scene_number": 1,
                "start_ms": 0,
                "end_ms": 2000,
                "asset_ref": {"media_asset_id": asset.id},
            }
        ),
    )
    service = TimelineRenderService(db_session)
    monkeypatch.setattr(service, "_render_to_temp_file", fake_render_to_temp_file)

    result = await service.process_render_job(job.id, user.id)

    assert result is not None
    assert result.status == "succeeded"
    assert result.output_asset_id is not None
    output_asset = db_session.get(MediaAsset, result.output_asset_id)
    assert output_asset is not None
    assert output_asset.origin == "rendered"
    assert output_asset.asset_type == "video"
    assert output_asset.file_url.endswith(".mp4")
    assert output_asset.extra_metadata["clip_ids"] == ["video_scene_1_beat_1_001"]
    output_link = (
        db_session.query(TimelineClipAsset)
        .filter(TimelineClipAsset.asset_role == "render_output")
        .one()
    )
    assert output_link.clip_id == "video_scene_1_beat_1_001"
    assert output_link.media_asset_id == output_asset.id
    assert output_link.render_job_id == result.id


@pytest.mark.asyncio
async def test_timeline_render_resolves_legacy_storyboard_video_by_timing(
    db_session,
    tmp_path,
    monkeypatch,
):
    output_path = tmp_path / "legacy-render.mp4"

    async def fake_render_to_temp_file(clips):
        assert [clip.source for clip in clips] == ["legacy_storyboard_timing"]
        assert clips[0].url == "https://example.com/legacy-frame.mp4"
        output_path.write_bytes(b"rendered video")
        return str(output_path)

    monkeypatch.setattr(
        "app.services.render.timeline_render_output.settings.UPLOAD_DIR",
        str(tmp_path / "uploads"),
    )
    user, _timeline, job = _bootstrap_timeline(
        db_session,
        spec=_spec_with_video_clip(
            {
                "clip_id": "video_scene_1_beat_10_001",
                "scene_number": 1,
                "start_ms": 1000,
                "end_ms": 2000,
            }
        ),
        storyboard_frames=[
            {
                "frame_id": "legacy-frame-1",
                "scene_number": 1,
                "frame_number": 1,
                "start_ms": 0,
                "end_ms": 2500,
                "video_url": "https://example.com/legacy-frame.mp4",
            }
        ],
    )
    service = TimelineRenderService(db_session)
    monkeypatch.setattr(service, "_render_to_temp_file", fake_render_to_temp_file)

    result = await service.process_render_job(job.id, user.id)

    assert result is not None
    assert result.status == "succeeded"
    output_asset = db_session.get(MediaAsset, result.output_asset_id)
    assert output_asset is not None
    assert output_asset.extra_metadata["clip_ids"] == ["video_scene_1_beat_10_001"]


@pytest.mark.asyncio
async def test_timeline_render_fails_with_missing_clip_videos(db_session):
    user, _timeline, job = _bootstrap_timeline(
        db_session,
        spec=_spec_with_video_clip(
            {
                "clip_id": "video_scene_2_beat_9_001",
                "scene_number": 2,
                "start_ms": 1000,
                "end_ms": 3000,
            }
        ),
    )

    result = await TimelineRenderService(db_session).process_render_job(job.id, user.id)

    assert result is not None
    assert result.status == "failed"
    assert result.log["code"] == "missing_clip_videos"
    assert result.log["missing_clips"][0]["clip_id"] == "video_scene_2_beat_9_001"


@pytest.mark.asyncio
async def test_timeline_render_fails_when_timeline_version_moved(db_session):
    user, timeline, job = _bootstrap_timeline(
        db_session,
        spec=_spec_with_video_clip(
            {
                "clip_id": "video_scene_1_beat_1_001",
                "video_url": "https://example.com/clip.mp4",
                "start_ms": 0,
                "end_ms": 1000,
            }
        ),
    )
    timeline.version = 2
    db_session.commit()

    result = await TimelineRenderService(db_session).process_render_job(job.id, user.id)

    assert result is not None
    assert result.status == "failed"
    assert result.log["code"] == "stale_timeline_version"
    assert result.log["current_version"] == 2
