import pytest
from app.models.timeline import MediaAsset, TimelineClipAsset
from app.services.render.timeline_render_service import TimelineRenderService
from tests.unit.services.render.test_timeline_render_service import (
    _bootstrap_timeline,
    _spec_with_video_clip,
)


@pytest.mark.asyncio
async def test_timeline_render_prefers_latest_generated_video_lineage(
    db_session,
    tmp_path,
    monkeypatch,
):
    output_path = tmp_path / "replacement-render.mp4"

    async def fake_render_to_temp_file(clips, _subtitles, _audio_track):
        assert clips[0].url == "https://example.com/generated-v2.mp4"
        assert clips[0].source == "timeline_clip_asset:provider_rework"
        output_path.write_bytes(b"rendered replacement video")
        return str(output_path)

    monkeypatch.setattr(
        "app.services.render.timeline_render_output.settings.UPLOAD_DIR",
        str(tmp_path / "uploads"),
    )
    original_asset = MediaAsset(
        asset_type="video",
        origin="ai_generated",
        file_url="https://example.com/generated-v1.mp4",
        mime_type="video/mp4",
    )
    replacement_asset = MediaAsset(
        asset_type="video",
        origin="provider_rework",
        file_url="https://example.com/generated-v2.mp4",
        mime_type="video/mp4",
    )
    db_session.add_all([original_asset, replacement_asset])
    db_session.commit()
    db_session.refresh(original_asset)
    db_session.refresh(replacement_asset)

    clip_id = "video_scene_1_beat_1_001"
    user, timeline, job = _bootstrap_timeline(
        db_session,
        spec=_spec_with_video_clip(
            {
                "clip_id": clip_id,
                "scene_number": 1,
                "start_ms": 0,
                "end_ms": 2000,
                "asset_ref": {"media_asset_id": original_asset.id},
            }
        ),
    )
    db_session.add(
        TimelineClipAsset(
            timeline_id=timeline.id,
            timeline_version=timeline.version,
            clip_id=clip_id,
            track_type="video",
            asset_role="generated_video",
            media_asset_id=replacement_asset.id,
            source="provider_rework",
            source_ref={"preserves_clip_id": True},
            created_by=user.id,
        )
    )
    db_session.commit()
    service = TimelineRenderService(db_session)
    monkeypatch.setattr(service, "_render_to_temp_file", fake_render_to_temp_file)

    result = await service.process_render_job(job.id, user.id)

    assert result is not None
    assert result.status == "succeeded"
