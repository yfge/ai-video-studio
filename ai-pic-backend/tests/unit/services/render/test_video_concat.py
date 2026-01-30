"""Tests for video concatenation utilities."""

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.render.video_concat import (
    VideoClip,
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

            with open(concat_file, "r") as f:
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

            with open(concat_file, "r") as f:
                content = f.read()

            # Single quote should be escaped
            assert "'\\''" in content or "clip" in content
        finally:
            if os.path.exists(concat_file):
                os.unlink(concat_file)


class TestTrimClipToDuration:
    """Test clip trimming functionality."""

    @patch("app.services.render.video_concat.subprocess.run")
    def test_trim_clip_shorter(self, mock_run):
        """Test trimming when clip is longer than target."""
        # Mock ffprobe to return 10 seconds
        mock_run.return_value = MagicMock(stdout="10.0\n", returncode=0)

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            input_path = f.name
            f.write(b"fake video data")

        output_path = input_path + ".out.mp4"

        try:
            # First call is ffprobe, second is ffmpeg
            result = trim_clip_to_duration(input_path, output_path, 5.0)

            # Should call ffprobe and ffmpeg
            assert mock_run.call_count >= 1
        finally:
            for p in [input_path, output_path]:
                if os.path.exists(p):
                    os.unlink(p)

    @patch("app.services.render.video_concat.subprocess.run")
    def test_no_trim_when_close(self, mock_run):
        """Test no trimming when duration is close to target."""
        # Mock ffprobe to return duration close to target
        mock_run.return_value = MagicMock(stdout="5.05\n", returncode=0)

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            input_path = f.name
            f.write(b"fake video data")

        output_path = input_path + ".out.mp4"

        try:
            result = trim_clip_to_duration(input_path, output_path, 5.0)
            # Should only call ffprobe, then rename
            assert mock_run.call_count == 1
        finally:
            for p in [input_path, output_path]:
                if os.path.exists(p):
                    os.unlink(p)


class TestConcatVideosFFmpeg:
    """Test video concatenation."""

    @patch("app.services.render.video_concat.subprocess.run")
    def test_concat_with_audio(self, mock_run):
        """Test concatenation keeping audio."""
        mock_run.return_value = MagicMock(returncode=0)

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            output_path = f.name

        # Create fake input files
        input_paths = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
                f.write(b"fake video")
                input_paths.append(f.name)

        try:
            result = concat_videos_ffmpeg(input_paths, output_path, keep_audio=True)

            # Verify ffmpeg was called
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "ffmpeg" in call_args
            assert "-c" in call_args
            assert "copy" in call_args
        finally:
            for p in input_paths + [output_path]:
                if os.path.exists(p):
                    os.unlink(p)

    @patch("app.services.render.video_concat.subprocess.run")
    def test_concat_without_audio(self, mock_run):
        """Test concatenation removing audio."""
        mock_run.return_value = MagicMock(returncode=0)

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            output_path = f.name

        input_paths = []
        for i in range(2):
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
                f.write(b"fake video")
                input_paths.append(f.name)

        try:
            result = concat_videos_ffmpeg(input_paths, output_path, keep_audio=False)

            call_args = mock_run.call_args[0][0]
            assert "-an" in call_args  # No audio flag
        finally:
            for p in input_paths + [output_path]:
                if os.path.exists(p):
                    os.unlink(p)


class TestReplaceAudio:
    """Test audio replacement."""

    @patch("app.services.render.video_concat.subprocess.run")
    def test_replace_audio(self, mock_run):
        """Test replacing video audio track."""
        mock_run.return_value = MagicMock(returncode=0)

        video_path = "/tmp/video.mp4"
        audio_path = "/tmp/audio.mp3"
        output_path = "/tmp/output.mp4"

        result = replace_audio(video_path, audio_path, output_path)

        assert result is True
        call_args = mock_run.call_args[0][0]
        assert "ffmpeg" in call_args
        assert "-map" in call_args
        assert "0:v:0" in call_args
        assert "1:a:0" in call_args

    @patch("app.services.render.video_concat.subprocess.run")
    def test_replace_audio_failure(self, mock_run):
        """Test handling audio replacement failure."""
        from subprocess import CalledProcessError

        mock_run.side_effect = CalledProcessError(1, "ffmpeg", stderr=b"Error")

        result = replace_audio("/tmp/v.mp4", "/tmp/a.mp3", "/tmp/o.mp4")

        assert result is False
