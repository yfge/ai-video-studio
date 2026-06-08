"""Tests for audio emotion normalization."""

from app.services.audio.audio_emotions import (
    ALLOWED_TTS_EMOTIONS,
    normalize_tts_emotion,
)


class TestAllowedTTSEmotions:
    """Tests for ALLOWED_TTS_EMOTIONS constant."""

    def test_contains_expected_emotions(self):
        """Test that all expected emotions are present."""
        expected = {
            "happy",
            "sad",
            "angry",
            "fearful",
            "disgusted",
            "surprised",
            "calm",
            "fluent",
            "whisper",
        }
        assert ALLOWED_TTS_EMOTIONS == expected

    def test_is_set(self):
        """Test that it's a set for O(1) lookup."""
        assert isinstance(ALLOWED_TTS_EMOTIONS, set)


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
        assert normalize_tts_emotion("说话", action="叹气") == "sad"
