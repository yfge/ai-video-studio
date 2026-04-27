"""Unit tests for audio generation utilities."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.services.audio.audio_generator import (
    download_to_file,
    ensure_oss_configured,
    generate_silence_wav,
    run_ffmpeg,
    tts_to_wav_file,
    wav_duration_ms,
)


class TestEnsureOSSConfigured:
    """Tests for ensure_oss_configured function."""

    def test_raises_when_none(self):
        """Test raises RuntimeError when OSS service is None."""
        with pytest.raises(RuntimeError, match="OSS service not configured"):
            ensure_oss_configured(None)

    def test_passes_when_configured(self):
        """Test passes when OSS service is provided."""
        oss_service = MagicMock()
        # Should not raise
        ensure_oss_configured(oss_service)


class TestWavDurationMs:
    """Tests for wav_duration_ms function."""

    def test_valid_wav_file(self, tmp_path):
        """Test getting duration from valid WAV file."""
        # Create a test WAV file using ffmpeg
        wav_path = tmp_path / "test.wav"
        with patch("app.services.audio.audio_generator.run_ffmpeg"):
            # Create a minimal WAV file manually
            import wave

            with wave.open(str(wav_path), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(24000)
                # Write 24000 frames = 1 second
                wf.writeframes(b"\x00\x00" * 24000)

            duration = wav_duration_ms(wav_path)
            assert duration == 1000  # 1 second


class TestRunFFmpeg:
    """Tests for run_ffmpeg function."""

    def test_successful_command(self):
        """Test successful ffmpeg command."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            # Should not raise
            run_ffmpeg(["ffmpeg", "-version"])

    def test_failed_command(self):
        """Test failed ffmpeg command raises."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stderr="Error: something went wrong"
            )
            with pytest.raises(RuntimeError, match="ffmpeg_failed"):
                run_ffmpeg(["ffmpeg", "-invalid"])


class TestGenerateSilenceWav:
    """Tests for generate_silence_wav function."""

    def test_generates_silence(self, tmp_path):
        """Test generating silent WAV file."""
        out_path = tmp_path / "silence.wav"
        with patch("app.services.audio.audio_generator.run_ffmpeg") as mock_ffmpeg:
            generate_silence_wav(out_path, duration_ms=1000)
            mock_ffmpeg.assert_called_once()
            # Check ffmpeg was called with correct duration
            args = mock_ffmpeg.call_args[0][0]
            assert "-t" in args
            assert "1.000" in args

    def test_zero_duration(self, tmp_path):
        """Test generating zero-duration silence."""
        out_path = tmp_path / "silence.wav"
        with patch("app.services.audio.audio_generator.run_ffmpeg") as mock_ffmpeg:
            generate_silence_wav(out_path, duration_ms=0)
            args = mock_ffmpeg.call_args[0][0]
            assert "0.000" in args


class TestDownloadToFile:
    """Tests for download_to_file function."""

    @pytest.mark.asyncio
    async def test_successful_download(self, tmp_path):
        """Test successful file download."""
        out_path = tmp_path / "downloaded.bin"
        mock_response = MagicMock()
        mock_response.content = b"test content"
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            await download_to_file("http://example.com/file", out_path)
            assert out_path.read_bytes() == b"test content"


class TestTTSToWavFile:
    """Tests for tts_to_wav_file function."""

    @pytest.mark.asyncio
    async def test_successful_tts(self, tmp_path):
        """Test successful TTS generation."""
        out_path = tmp_path / "speech.wav"
        voice_config = {
            "provider": "minimax",
            "tts_model": "speech-2.6-hd",
            "voice_id": "test_voice",
        }

        mock_response = MagicMock()
        mock_response.success = True
        mock_response.data = {"audio_url": "http://example.com/audio.wav"}

        with patch("app.services.audio.audio_generator.ai_service") as mock_ai:
            mock_ai.ai_manager.text_to_speech = AsyncMock(return_value=mock_response)
            with patch(
                "app.services.audio.audio_generator.download_to_file"
            ) as mock_download:
                mock_download.return_value = None
                await tts_to_wav_file(
                    text="Hello world",
                    voice_config=voice_config,
                    out_path=out_path,
                )
                mock_download.assert_called_once()

    @pytest.mark.asyncio
    async def test_tts_no_ai_manager(self, tmp_path):
        """Test TTS fails without AI manager."""
        out_path = tmp_path / "speech.wav"
        voice_config = {"provider": "minimax"}

        with patch("app.services.audio.audio_generator.ai_service") as mock_ai:
            mock_ai.ai_manager = None
            with pytest.raises(RuntimeError, match="AI manager not initialized"):
                await tts_to_wav_file(
                    text="Hello",
                    voice_config=voice_config,
                    out_path=out_path,
                )

    @pytest.mark.asyncio
    async def test_tts_failure(self, tmp_path):
        """Test TTS failure handling."""
        out_path = tmp_path / "speech.wav"
        voice_config = {"provider": "minimax"}

        mock_response = MagicMock()
        mock_response.success = False
        mock_response.error = "TTS error"

        with patch("app.services.audio.audio_generator.ai_service") as mock_ai:
            mock_ai.ai_manager.text_to_speech = AsyncMock(return_value=mock_response)
            with pytest.raises(RuntimeError, match="TTS error"):
                await tts_to_wav_file(
                    text="Hello",
                    voice_config=voice_config,
                    out_path=out_path,
                )
