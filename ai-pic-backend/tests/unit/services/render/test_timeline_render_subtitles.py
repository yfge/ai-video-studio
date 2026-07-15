from pathlib import Path

import pytest
from app.services.render.timeline_render_service import TimelineRenderService
from app.services.render.video_concat import (
    VideoClip,
    VideoSubtitleCue,
    concat_video_clips,
)
from tests.unit.services.render.test_timeline_render_service import (
    _bootstrap_timeline,
    _spec_with_video_clip,
)


@pytest.mark.asyncio
async def test_timeline_render_passes_subtitle_track_to_composer(
    db_session,
    tmp_path,
    monkeypatch,
):
    output_path = tmp_path / "subtitle-render.mp4"

    async def fake_render_to_temp_file(clips, subtitles, _audio_track, *, render_spec):
        assert render_spec.fps == 24
        assert [clip.clip_id for clip in clips] == ["video_scene_1_beat_1_001"]
        assert len(subtitles) == 1
        assert subtitles[0].text == "小蓝: 我到了。"
        assert subtitles[0].start_ms == 0
        assert subtitles[0].end_ms == 2000
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
    spec["tracks"].append(
        {
            "track_type": "subtitle",
            "clips": [
                {
                    "clip_id": "subtitle_scene_1_beat_1_001",
                    "text": "小蓝: 我到了。",
                    "start_ms": 0,
                    "end_ms": 2000,
                }
            ],
        }
    )
    user, _timeline, job = _bootstrap_timeline(db_session, spec=spec)
    service = TimelineRenderService(db_session)
    monkeypatch.setattr(service, "_render_to_temp_file", fake_render_to_temp_file)

    result = await service.process_render_job(job.id, user.id)

    assert result is not None
    assert result.status == "succeeded"
    assert result.log["subtitle_count"] == 1


@pytest.mark.asyncio
async def test_concat_video_clips_burns_subtitle_cues(tmp_path, monkeypatch):
    captured = {}

    async def fake_download_all_clips(_clips, work_dir):
        raw_path = Path(work_dir) / "raw.mp4"
        raw_path.write_bytes(b"raw")
        return [str(raw_path)]

    def fake_trim(_raw_path, trimmed_path, _duration):
        Path(trimmed_path).write_bytes(b"trimmed")
        return True

    def fake_concat(_paths, concat_output, _keep_audio):
        Path(concat_output).write_bytes(b"concat")
        return True

    def fake_burn(_video_path, subtitle_path, output_path):
        captured["srt"] = Path(subtitle_path).read_text(encoding="utf-8")
        Path(output_path).write_bytes(b"subtitled")
        return True

    monkeypatch.setattr(
        "app.services.render.video_concat.download_all_clips",
        fake_download_all_clips,
    )
    monkeypatch.setattr(
        "app.services.render.video_concat.trim_clip_to_duration", fake_trim
    )
    monkeypatch.setattr(
        "app.services.render.video_concat.concat_videos_ffmpeg", fake_concat
    )
    monkeypatch.setattr(
        "app.services.render.video_concat.burn_subtitles_ffmpeg", fake_burn
    )

    result = await concat_video_clips(
        [VideoClip("https://example.com/a.mp4", 2.0, 1)],
        str(tmp_path / "render.mp4"),
        subtitles=[VideoSubtitleCue("小蓝: 我到了。", 0, 2)],
    )

    assert result["success"] is True
    assert result["has_burned_subtitles"] is True
    assert result["subtitle_count"] == 1
    assert "00:00:00,000 --> 00:00:02,000" in captured["srt"]
    assert "小蓝: 我到了。" in captured["srt"]
