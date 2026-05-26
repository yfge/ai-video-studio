"""Tests for video concatenation utilities."""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from app.services.render.video_concat import (
    VideoAudioSegment,
    VideoClip,
    burn_subtitles_ffmpeg,
    compose_audio_segments_ffmpeg,
    concat_video_clips,
    concat_videos_ffmpeg,
    create_concat_file,
    replace_audio,
    trim_clip_to_duration,
)


class TestVideoClip:
    """Test VideoClip dataclass."""

    def test_create_clip(self):
        """Test creating a VideoClip."""
        clip = VideoClip(
            url="https://example.com/video.mp4",
            target_duration_seconds=5.0,
            frame_number=1,
            description="Test frame",
        )
        assert clip.url == "https://example.com/video.mp4"
        assert clip.target_duration_seconds == 5.0
        assert clip.frame_number == 1
        assert clip.description == "Test frame"

    def test_clip_without_description(self):
        """Test creating clip without optional fields."""
        clip = VideoClip(
            url="https://example.com/video.mp4",
            target_duration_seconds=3.0,
            frame_number=2,
        )
        assert clip.description is None


class TestCreateConcatFile:
    """Test concat file creation."""

    def test_create_concat_file(self):
        """Test creating ffmpeg concat demuxer file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            concat_file = f.name

        try:
            clip_paths = ["/tmp/clip1.mp4", "/tmp/clip2.mp4", "/tmp/clip3.mp4"]
            create_concat_file(clip_paths, concat_file)

            with open(concat_file) as f:
                content = f.read()

            assert "file '/tmp/clip1.mp4'" in content
            assert "file '/tmp/clip2.mp4'" in content
            assert "file '/tmp/clip3.mp4'" in content
        finally:
            if os.path.exists(concat_file):
                os.unlink(concat_file)

    def test_escape_single_quotes(self):
        """Test that single quotes are escaped."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            concat_file = f.name

        try:
            clip_paths = ["/tmp/clip's.mp4"]
            create_concat_file(clip_paths, concat_file)

            with open(concat_file) as f:
                content = f.read()

            assert "'\\''" in content or "clip" in content
        finally:
            if os.path.exists(concat_file):
                os.unlink(concat_file)


class TestTrimClipToDuration:
    """Test clip trimming functionality."""

    @patch("app.services.render.video_ffmpeg.subprocess.run")
    def test_trim_clip_shorter(self, mock_run):
        """Test trimming when clip is longer than target."""
        mock_run.return_value = MagicMock(stdout="10.0\n", returncode=0)

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            input_path = f.name
            f.write(b"fake video data")

        output_path = input_path + ".out.mp4"

        try:
            trim_clip_to_duration(input_path, output_path, 5.0)

            assert mock_run.call_count >= 1
        finally:
            for path in [input_path, output_path]:
                if os.path.exists(path):
                    os.unlink(path)

    @patch("app.services.render.video_ffmpeg.subprocess.run")
    def test_no_trim_when_close(self, mock_run):
        """Test no trimming when duration is close to target."""
        mock_run.return_value = MagicMock(stdout="5.05\n", returncode=0)

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            input_path = f.name
            f.write(b"fake video data")

        output_path = input_path + ".out.mp4"

        try:
            trim_clip_to_duration(input_path, output_path, 5.0)

            assert mock_run.call_count == 1
        finally:
            for path in [input_path, output_path]:
                if os.path.exists(path):
                    os.unlink(path)


class TestConcatVideosFFmpeg:
    """Test video concatenation."""

    @patch("app.services.render.video_ffmpeg.subprocess.run")
    def test_concat_with_audio(self, mock_run):
        """Test concatenation keeping audio."""
        mock_run.return_value = MagicMock(returncode=0)

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            output_path = f.name

        input_paths = []
        for _ in range(3):
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
                f.write(b"fake video")
                input_paths.append(f.name)

        try:
            concat_videos_ffmpeg(input_paths, output_path, keep_audio=True)

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "ffmpeg" in call_args
            assert "-c" in call_args
            assert "copy" in call_args
        finally:
            for path in input_paths + [output_path]:
                if os.path.exists(path):
                    os.unlink(path)

    @patch("app.services.render.video_ffmpeg.subprocess.run")
    def test_concat_without_audio(self, mock_run):
        """Test concatenation removing audio."""
        mock_run.return_value = MagicMock(returncode=0)

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            output_path = f.name

        input_paths = []
        for _ in range(2):
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
                f.write(b"fake video")
                input_paths.append(f.name)

        try:
            concat_videos_ffmpeg(input_paths, output_path, keep_audio=False)

            call_args = mock_run.call_args[0][0]
            assert "-an" in call_args
        finally:
            for path in input_paths + [output_path]:
                if os.path.exists(path):
                    os.unlink(path)


class TestReplaceAudio:
    """Test audio replacement."""

    @patch("app.services.render.video_ffmpeg.subprocess.run")
    def test_replace_audio(self, mock_run):
        """Test replacing video audio track."""
        mock_run.return_value = MagicMock(returncode=0)

        result = replace_audio("/tmp/video.mp4", "/tmp/audio.mp3", "/tmp/output.mp4")

        assert result is True
        call_args = mock_run.call_args[0][0]
        assert "ffmpeg" in call_args
        assert "-filter_complex" in call_args
        assert "[1:a]apad[a]" in call_args
        assert "-map" in call_args
        assert "0:v:0" in call_args
        assert "[a]" in call_args

    @patch("app.services.render.video_ffmpeg.subprocess.run")
    def test_replace_audio_failure(self, mock_run):
        """Test handling audio replacement failure."""
        from subprocess import CalledProcessError

        mock_run.side_effect = CalledProcessError(1, "ffmpeg", stderr=b"Error")

        result = replace_audio("/tmp/v.mp4", "/tmp/a.mp3", "/tmp/o.mp4")

        assert result is False


class TestComposeAudioSegments:
    """Test timeline audio segment composition."""

    @patch("app.services.render.video_ffmpeg.subprocess.run")
    def test_compose_audio_segments_bounds_output_duration(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)

        result = compose_audio_segments_ffmpeg(
            ["/tmp/a.mp3", "/tmp/b.mp3"],
            [0, 1.5],
            [1.2, 2.0],
            "/tmp/out.m4a",
        )

        assert result is True
        call_args = mock_run.call_args[0][0]
        assert "-t" in call_args
        assert call_args[call_args.index("-t") + 1] == "3.500"


class TestBurnSubtitles:
    """Test subtitle burn command construction."""

    @patch("app.services.render.video_ffmpeg.subprocess.run")
    def test_burn_subtitles_uses_cjk_font(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)

        result = burn_subtitles_ffmpeg("/tmp/video.mp4", "/tmp/sub.srt", "/tmp/out.mp4")

        assert result is True
        call_args = mock_run.call_args[0][0]
        video_filter = call_args[call_args.index("-vf") + 1]
        assert "FontName=Noto Sans CJK SC" in video_filter


@pytest.mark.asyncio
async def test_concat_video_clips_composes_timeline_audio_segments(
    tmp_path, monkeypatch
):
    """Timeline dialogue audio is mixed by clip timing before replacement."""
    captured: dict[str, object] = {}

    async def fake_download_all_clips(clips, work_dir):
        paths = []
        for index, _clip in enumerate(clips):
            path = os.path.join(work_dir, f"raw-{index}.mp4")
            with open(path, "wb") as file:
                file.write(b"raw video")
            paths.append(path)
        return paths

    def fake_trim_clip_to_duration(raw_path, output_path, _duration):
        with open(output_path, "wb") as file:
            file.write(b"trimmed video")
        return True

    def fake_concat_videos_ffmpeg(paths, output_path, keep_audio):
        captured["keep_audio"] = keep_audio
        captured["concat_paths"] = paths
        with open(output_path, "wb") as file:
            file.write(b"concat video")
        return True

    async def fake_download_url(url):
        return f"audio:{url}".encode()

    def fake_compose_audio_segments_ffmpeg(paths, starts, durations, output_path):
        captured["audio_paths"] = paths
        captured["starts"] = starts
        captured["durations"] = durations
        with open(output_path, "wb") as file:
            file.write(b"mixed audio")
        return True

    def fake_replace_audio(video_path, audio_path, output_path):
        captured["replace_video"] = video_path
        captured["replace_audio"] = audio_path
        with open(output_path, "wb") as file:
            file.write(b"rendered video")
        return True

    monkeypatch.setattr(
        "app.services.render.video_concat.download_all_clips",
        fake_download_all_clips,
    )
    monkeypatch.setattr(
        "app.services.render.video_concat.trim_clip_to_duration",
        fake_trim_clip_to_duration,
    )
    monkeypatch.setattr(
        "app.services.render.video_concat.concat_videos_ffmpeg",
        fake_concat_videos_ffmpeg,
    )
    monkeypatch.setattr(
        "app.services.render.video_concat.download_url",
        fake_download_url,
    )
    monkeypatch.setattr(
        "app.services.render.video_concat.compose_audio_segments_ffmpeg",
        fake_compose_audio_segments_ffmpeg,
    )
    monkeypatch.setattr(
        "app.services.render.video_concat.replace_audio",
        fake_replace_audio,
    )

    result = await concat_video_clips(
        clips=[
            VideoClip(
                url="https://example.com/video-1.mp4",
                target_duration_seconds=2.0,
                frame_number=1,
            )
        ],
        output_path=str(tmp_path / "output.mp4"),
        audio_segments=[
            VideoAudioSegment(
                url="https://example.com/dialogue-1.mp3",
                start_seconds=0,
                end_seconds=1.2,
            ),
            VideoAudioSegment(
                url="https://example.com/dialogue-2.mp3",
                start_seconds=1.5,
                end_seconds=2.0,
            ),
        ],
        keep_original_audio=False,
    )

    assert result["success"] is True
    assert result["has_replaced_audio"] is True
    assert result["audio_segment_count"] == 2
    assert captured["keep_audio"] is False
    assert captured["starts"] == [0, 1.5]
    assert captured["durations"] == [1.2, 0.5]
    assert str(captured["replace_audio"]).endswith("timeline_audio.m4a")
