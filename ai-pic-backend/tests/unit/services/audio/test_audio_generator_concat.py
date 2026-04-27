"""Tests for audio generation concatenation helpers."""

from unittest.mock import patch

import pytest
from app.services.audio.audio_generator import concat_mp3s, concat_wavs, encode_mp3


class TestConcatWavs:
    """Tests for concat_wavs function."""

    def test_concat_files(self, tmp_path):
        """Test concatenating WAV files."""
        wav1 = tmp_path / "1.wav"
        wav2 = tmp_path / "2.wav"
        out_wav = tmp_path / "output.wav"

        with patch("app.services.audio.audio_generator.run_ffmpeg") as mock_ffmpeg:
            concat_wavs([wav1, wav2], out_wav)
            mock_ffmpeg.assert_called_once()
            assert (tmp_path / "concat.txt").exists()


class TestEncodeMp3:
    """Tests for encode_mp3 function."""

    def test_encode_mp3(self, tmp_path):
        """Test encoding WAV to MP3."""
        in_wav = tmp_path / "input.wav"
        out_mp3 = tmp_path / "output.mp3"

        with patch("app.services.audio.audio_generator.run_ffmpeg") as mock_ffmpeg:
            encode_mp3(in_wav, out_mp3)
            mock_ffmpeg.assert_called_once()
            args = mock_ffmpeg.call_args[0][0]
            assert "-acodec" in args
            assert "libmp3lame" in args

    def test_encode_mp3_custom_bitrate(self, tmp_path):
        """Test encoding with custom bitrate."""
        in_wav = tmp_path / "input.wav"
        out_mp3 = tmp_path / "output.mp3"

        with patch("app.services.audio.audio_generator.run_ffmpeg") as mock_ffmpeg:
            encode_mp3(in_wav, out_mp3, bitrate="256k")
            args = mock_ffmpeg.call_args[0][0]
            assert "256k" in args


class TestConcatMp3s:
    """Tests for concat_mp3s function."""

    def test_concat_mp3s_normalizes_and_encodes_once(self, tmp_path):
        """Test MP3 concat decodes to WAV before final MP3 encode."""
        mp3_1 = tmp_path / "1.mp3"
        mp3_2 = tmp_path / "2.mp3"
        out_mp3 = tmp_path / "output.mp3"

        with patch("app.services.audio.audio_generator.run_ffmpeg") as mock_ffmpeg:
            concat_mp3s([mp3_1, mp3_2], out_mp3)

        assert mock_ffmpeg.call_count == 4
        first_args = mock_ffmpeg.call_args_list[0][0][0]
        concat_args = mock_ffmpeg.call_args_list[2][0][0]
        final_args = mock_ffmpeg.call_args_list[3][0][0]
        assert str(mp3_1) in first_args
        assert any("concat-merged.wav" in item for item in final_args)
        assert "libmp3lame" in final_args
        assert "copy" not in concat_args

    def test_concat_mp3s_rejects_empty_input(self, tmp_path):
        """Test empty MP3 lists are rejected."""
        with pytest.raises(RuntimeError, match="no_mp3s_to_concat"):
            concat_mp3s([], tmp_path / "output.mp3")
