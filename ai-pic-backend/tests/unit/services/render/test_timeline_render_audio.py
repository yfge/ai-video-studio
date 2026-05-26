import pytest
from app.services.render.timeline_render_audio import resolve_timeline_audio_track
from app.services.render.timeline_render_service import TimelineRenderService
from tests.unit.services.render.test_timeline_render_service import (
    _bootstrap_timeline,
    _spec_with_video_clip,
)


@pytest.mark.asyncio
async def test_timeline_render_passes_source_audio_to_composer(
    db_session,
    tmp_path,
    monkeypatch,
):
    output_path = tmp_path / "audio-render.mp4"

    async def fake_render_to_temp_file(_clips, _subtitles, audio_track):
        assert audio_track is not None
        assert audio_track.url == "https://example.com/dialogue.mp3"
        assert audio_track.source == "timeline.source.episode_audio"
        output_path.write_bytes(b"rendered video")
        return str(output_path)

    monkeypatch.setattr(
        "app.services.render.timeline_render_output.settings.UPLOAD_DIR",
        str(tmp_path / "uploads"),
    )
    spec = _spec_with_video_clip(
        {
            "clip_id": "video_scene_1_beat_1_001",
            "video_url": "https://example.com/clip.mp4",
            "start_ms": 0,
            "end_ms": 2000,
        }
    )
    spec["source"] = {
        "type": "audio_timeline",
        "episode_audio": {"oss_url": "https://example.com/dialogue.mp3"},
    }
    user, _timeline, job = _bootstrap_timeline(db_session, spec=spec)
    service = TimelineRenderService(db_session)
    monkeypatch.setattr(service, "_render_to_temp_file", fake_render_to_temp_file)

    result = await service.process_render_job(job.id, user.id)

    assert result is not None
    assert result.status == "succeeded"
    assert result.log["has_replaced_audio"] is True
    assert result.log["audio_source"] == "timeline.source.episode_audio"


def test_resolve_timeline_audio_track_from_dialogue_asset_ref(db_session):
    spec = _spec_with_video_clip(
        {
            "clip_id": "video_scene_1_beat_1_001",
            "video_url": "https://example.com/clip.mp4",
            "start_ms": 0,
            "end_ms": 2000,
        }
    )
    spec["tracks"].append(
        {
            "track_type": "dialogue",
            "clips": [
                {
                    "clip_id": "dialogue_scene_1_beat_1_001",
                    "start_ms": 0,
                    "end_ms": 2000,
                    "asset_ref": {
                        "kind": "provider_chain_dialogue_audio",
                        "url": "https://example.com/dialogue.mp3",
                    },
                }
            ],
        }
    )
    _user, timeline, _job = _bootstrap_timeline(db_session, spec=spec)

    audio_track = resolve_timeline_audio_track(timeline)

    assert audio_track is not None
    assert audio_track.url is None
    assert audio_track.source == "timeline.dialogue.asset_ref"
    assert audio_track.clip_count == 1
    assert len(audio_track.segments) == 1
    assert audio_track.segments[0].url == "https://example.com/dialogue.mp3"
    assert audio_track.segments[0].start_ms == 0
    assert audio_track.segments[0].end_ms == 2000
    assert audio_track.segments[0].clip_id == "dialogue_scene_1_beat_1_001"


def test_resolve_timeline_audio_track_preserves_dialogue_segment_timing(db_session):
    spec = _spec_with_video_clip(
        {
            "clip_id": "video_scene_1_beat_1_001",
            "video_url": "https://example.com/clip.mp4",
            "start_ms": 0,
            "end_ms": 3000,
        }
    )
    spec["tracks"].append(
        {
            "track_type": "dialogue",
            "clips": [
                {
                    "clip_id": "dialogue_scene_1_beat_1_001",
                    "start_ms": 0,
                    "end_ms": 1200,
                    "asset_ref": {"url": "https://example.com/dialogue-1.mp3"},
                },
                {
                    "clip_id": "dialogue_scene_1_beat_2_002",
                    "start_ms": 1500,
                    "end_ms": 3000,
                    "asset_ref": {"url": "https://example.com/dialogue-2.mp3"},
                },
            ],
        }
    )
    _user, timeline, _job = _bootstrap_timeline(db_session, spec=spec)

    audio_track = resolve_timeline_audio_track(timeline)

    assert audio_track is not None
    assert audio_track.source == "timeline.dialogue.asset_ref"
    assert audio_track.url is None
    assert audio_track.clip_count == 2
    assert [(s.url, s.start_ms, s.end_ms) for s in audio_track.segments] == [
        ("https://example.com/dialogue-1.mp3", 0, 1200),
        ("https://example.com/dialogue-2.mp3", 1500, 3000),
    ]


def test_resolve_timeline_audio_track_ignores_partial_dialogue_assets(db_session):
    spec = _spec_with_video_clip(
        {
            "clip_id": "video_scene_1_beat_1_001",
            "video_url": "https://example.com/clip.mp4",
            "start_ms": 0,
            "end_ms": 2000,
        }
    )
    spec["tracks"].append(
        {
            "track_type": "dialogue",
            "clips": [
                {
                    "clip_id": "dialogue_scene_1_beat_1_001",
                    "start_ms": 0,
                    "end_ms": 1000,
                    "asset_ref": {"url": "https://example.com/dialogue.mp3"},
                },
                {
                    "clip_id": "dialogue_scene_1_beat_2_002",
                    "start_ms": 1000,
                    "end_ms": 2000,
                },
            ],
        }
    )
    _user, timeline, _job = _bootstrap_timeline(db_session, spec=spec)

    assert resolve_timeline_audio_track(timeline) is None
