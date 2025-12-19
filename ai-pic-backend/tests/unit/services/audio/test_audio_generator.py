"""Unit tests for audio generation utilities."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

from app.services.audio.audio_generator import (
    ALLOWED_TTS_EMOTIONS,
    ensure_oss_configured,
    wav_duration_ms,
    run_ffmpeg,
    generate_silence_wav,
    download_to_file,
    tts_to_wav_file,
    normalize_tts_emotion,
    concat_wavs,
    encode_mp3,
    concat_mp3s,
)


class TestAllowedTTSEmotions:
    """Tests for ALLOWED_TTS_EMOTIONS constant."""

    def test_contains_expected_emotions(self):
        """Test that all expected emotions are present."""
        expected = {
            "happy", "sad", "angry", "fearful", "disgusted",
            "surprised", "calm", "fluent", "whisper",
        }
        assert ALLOWED_TTS_EMOTIONS == expected

    def test_is_set(self):
        """Test that it's a set for O(1) lookup."""
        assert isinstance(ALLOWED_TTS_EMOTIONS, set)


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


class TestNormalizeTTSEmotion:
    """Tests for normalize_tts_emotion function."""

    def test_direct_emotion_match(self):
        """Test direct emotion string matching."""
        assert normalize_tts_emotion("happy") == "happy"
        assert normalize_tts_emotion("sad") == "sad"
        assert normalize_tts_emotion("ANGRY") == "angry"

    def test_whisper_detection(self):
        """Test whisper-related emotion detection."""
        assert normalize_tts_emotion("低声说") == "whisper"
        assert normalize_tts_emotion("悄声说") == "whisper"
        assert normalize_tts_emotion(None, action="小声说") == "whisper"
        assert normalize_tts_emotion("低语") == "whisper"

    def test_angry_detection(self):
        """Test angry-related emotion detection."""
        assert normalize_tts_emotion("愤怒地") == "angry"
        assert normalize_tts_emotion("生气") == "angry"
        assert normalize_tts_emotion(None, action="暴躁") == "angry"

    def test_sad_detection(self):
        """Test sad-related emotion detection."""
        assert normalize_tts_emotion("悲伤") == "sad"
        assert normalize_tts_emotion("难过") == "sad"
        assert normalize_tts_emotion(None, action="叹气") == "sad"
        assert normalize_tts_emotion(None, action="叹了一口气") == "sad"

    def test_happy_detection(self):
        """Test happy-related emotion detection."""
        assert normalize_tts_emotion("高兴") == "happy"
        assert normalize_tts_emotion("开心") == "happy"
        assert normalize_tts_emotion(None, action="兴奋") == "happy"

    def test_surprised_detection(self):
        """Test surprised-related emotion detection."""
        assert normalize_tts_emotion("惊讶") == "surprised"
        assert normalize_tts_emotion("震惊") == "surprised"

    def test_fearful_detection(self):
        """Test fearful-related emotion detection."""
        assert normalize_tts_emotion("害怕") == "fearful"
        assert normalize_tts_emotion("恐惧") == "fearful"
        assert normalize_tts_emotion(None, action="紧张") == "fearful"

    def test_disgusted_detection(self):
        """Test disgusted-related emotion detection."""
        assert normalize_tts_emotion("厌恶") == "disgusted"
        assert normalize_tts_emotion("恶心") == "disgusted"

    def test_calm_detection(self):
        """Test calm-related emotion detection."""
        assert normalize_tts_emotion("平静") == "calm"
        assert normalize_tts_emotion("冷静") == "calm"
        assert normalize_tts_emotion(None, action="沉稳") == "calm"

    def test_fluent_detection(self):
        """Test fluent-related emotion detection."""
        assert normalize_tts_emotion("自信") == "fluent"
        assert normalize_tts_emotion("坚定") == "fluent"
        assert normalize_tts_emotion(None, action="从容") == "fluent"

    def test_none_values(self):
        """Test None inputs return None."""
        assert normalize_tts_emotion(None) is None
        assert normalize_tts_emotion(None, action=None) is None

    def test_empty_strings(self):
        """Test empty strings return None."""
        assert normalize_tts_emotion("") is None
        assert normalize_tts_emotion("", action="") is None

    def test_unrecognized_emotion(self):
        """Test unrecognized emotion returns None."""
        assert normalize_tts_emotion("unknown_emotion") is None
        assert normalize_tts_emotion("一些随机文字") is None

    def test_combined_emotion_and_action(self):
        """Test emotion detection from combined text."""
        # Action takes effect when emotion alone doesn't match
        assert normalize_tts_emotion("说话", action="叹气") == "sad"


class TestWavDurationMs:
    """Tests for wav_duration_ms function."""

    def test_valid_wav_file(self, tmp_path):
        """Test getting duration from valid WAV file."""
        # Create a test WAV file using ffmpeg
        wav_path = tmp_path / "test.wav"
        with patch("app.services.audio.audio_generator.run_ffmpeg") as mock_ffmpeg:
            # Create a minimal WAV file manually
            import wave
            with wave.open(str(wav_path), 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(24000)
                # Write 24000 frames = 1 second
                wf.writeframes(b'\x00\x00' * 24000)

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
                returncode=1,
                stderr="Error: something went wrong"
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
            # Check concat file was created
            concat_file = tmp_path / "concat.txt"
            assert concat_file.exists()


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

    def test_concat_mp3s(self, tmp_path):
        """Test concatenating MP3 files."""
        mp3_1 = tmp_path / "1.mp3"
        mp3_2 = tmp_path / "2.mp3"
        out_mp3 = tmp_path / "output.mp3"

        with patch("app.services.audio.audio_generator.run_ffmpeg") as mock_ffmpeg:
            concat_mp3s([mp3_1, mp3_2], out_mp3)
            mock_ffmpeg.assert_called_once()
            # Should use copy codec for MP3s
            args = mock_ffmpeg.call_args[0][0]
            assert "-acodec" in args
            assert "copy" in args
