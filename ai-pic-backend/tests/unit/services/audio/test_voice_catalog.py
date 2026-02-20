"""Unit tests for voice catalog and constants."""

from app.services.audio.voice_catalog import (
    SYSTEM_VOICE_CATALOG as AUDIO_SYSTEM_VOICE_CATALOG,
)
from app.services.audio.voice_constants import (
    AUDIO_FORMAT_OPTIONS,
    CHANNEL_OPTIONS,
    DEFAULT_MINIMAX_VOICE_ID,
    EMOTION_OPTIONS,
    LANGUAGE_BOOST_OPTIONS,
    SAMPLE_RATE_OPTIONS,
    TTS_MODEL_OPTIONS,
    VOICE_TYPE_OPTIONS,
)
from app.services.voice_catalog import SYSTEM_VOICE_CATALOG


class TestSystemVoiceCatalog:
    """Tests for SYSTEM_VOICE_CATALOG constant."""

    def test_audio_wrapper_aliases_core_catalog(self):
        """Test that the compatibility wrapper points to the same list object."""
        assert AUDIO_SYSTEM_VOICE_CATALOG is SYSTEM_VOICE_CATALOG

    def test_is_list(self):
        """Test that catalog is a list."""
        assert isinstance(SYSTEM_VOICE_CATALOG, list)

    def test_has_voices(self):
        """Test that catalog has voices."""
        assert len(SYSTEM_VOICE_CATALOG) > 0

    def test_voice_structure(self):
        """Test that each voice has required fields."""
        for voice in SYSTEM_VOICE_CATALOG:
            assert isinstance(voice, dict)
            assert "voice_id" in voice
            assert "voice_name" in voice
            assert "language" in voice

    def test_voice_id_unique(self):
        """Test that voice IDs are unique."""
        voice_ids = [v["voice_id"] for v in SYSTEM_VOICE_CATALOG]
        assert len(voice_ids) == len(set(voice_ids))

    def test_has_chinese_voices(self):
        """Test that catalog has Chinese voices."""
        chinese_voices = [v for v in SYSTEM_VOICE_CATALOG if v["language"] == "zh-CN"]
        assert len(chinese_voices) > 0

    def test_has_english_voices(self):
        """Test that catalog has English voices."""
        english_voices = [v for v in SYSTEM_VOICE_CATALOG if v["language"] == "en"]
        assert len(english_voices) > 0


class TestDefaultVoiceId:
    """Tests for DEFAULT_MINIMAX_VOICE_ID constant."""

    def test_is_string(self):
        """Test that default voice ID is a string."""
        assert isinstance(DEFAULT_MINIMAX_VOICE_ID, str)

    def test_not_empty(self):
        """Test that default voice ID is not empty."""
        assert len(DEFAULT_MINIMAX_VOICE_ID) > 0

    def test_exists_in_catalog(self):
        """Test that default voice ID exists in catalog."""
        voice_ids = {v["voice_id"] for v in SYSTEM_VOICE_CATALOG}
        assert DEFAULT_MINIMAX_VOICE_ID in voice_ids


class TestVoiceTypeOptions:
    """Tests for VOICE_TYPE_OPTIONS constant."""

    def test_is_list(self):
        """Test that voice type options is a list."""
        assert isinstance(VOICE_TYPE_OPTIONS, list)

    def test_has_options(self):
        """Test that options exist."""
        assert len(VOICE_TYPE_OPTIONS) > 0

    def test_option_structure(self):
        """Test that each option has required fields."""
        for opt in VOICE_TYPE_OPTIONS:
            assert "value" in opt
            assert "label_zh" in opt
            assert "label_en" in opt

    def test_has_system_type(self):
        """Test that system voice type exists."""
        values = [opt["value"] for opt in VOICE_TYPE_OPTIONS]
        assert "system" in values

    def test_has_all_type(self):
        """Test that 'all' voice type exists."""
        values = [opt["value"] for opt in VOICE_TYPE_OPTIONS]
        assert "all" in values


class TestTTSModelOptions:
    """Tests for TTS_MODEL_OPTIONS constant."""

    def test_is_list(self):
        """Test that TTS model options is a list."""
        assert isinstance(TTS_MODEL_OPTIONS, list)

    def test_has_options(self):
        """Test that options exist."""
        assert len(TTS_MODEL_OPTIONS) > 0

    def test_option_structure(self):
        """Test that each option has required fields."""
        for opt in TTS_MODEL_OPTIONS:
            assert "value" in opt
            assert "label_zh" in opt
            assert "label_en" in opt

    def test_has_hd_models(self):
        """Test that HD models exist."""
        values = [opt["value"] for opt in TTS_MODEL_OPTIONS]
        hd_models = [v for v in values if "hd" in v.lower()]
        assert len(hd_models) > 0


class TestEmotionOptions:
    """Tests for EMOTION_OPTIONS constant."""

    def test_is_list(self):
        """Test that emotion options is a list."""
        assert isinstance(EMOTION_OPTIONS, list)

    def test_has_nine_emotions(self):
        """Test that there are 9 emotion options."""
        assert len(EMOTION_OPTIONS) == 9

    def test_has_basic_emotions(self):
        """Test that basic emotions exist."""
        values = [opt["value"] for opt in EMOTION_OPTIONS]
        assert "happy" in values
        assert "sad" in values
        assert "angry" in values
        assert "calm" in values

    def test_option_structure(self):
        """Test that each option has required fields."""
        for opt in EMOTION_OPTIONS:
            assert "value" in opt
            assert "label_zh" in opt
            assert "label_en" in opt


class TestLanguageBoostOptions:
    """Tests for LANGUAGE_BOOST_OPTIONS constant."""

    def test_is_list(self):
        """Test that language boost options is a list."""
        assert isinstance(LANGUAGE_BOOST_OPTIONS, list)

    def test_has_options(self):
        """Test that options exist."""
        assert len(LANGUAGE_BOOST_OPTIONS) > 0

    def test_has_chinese(self):
        """Test that Chinese language exists."""
        values = [opt["value"] for opt in LANGUAGE_BOOST_OPTIONS]
        assert "Chinese" in values

    def test_has_english(self):
        """Test that English language exists."""
        values = [opt["value"] for opt in LANGUAGE_BOOST_OPTIONS]
        assert "English" in values

    def test_has_auto(self):
        """Test that auto detection exists."""
        values = [opt["value"] for opt in LANGUAGE_BOOST_OPTIONS]
        assert "auto" in values


class TestAudioFormatOptions:
    """Tests for AUDIO_FORMAT_OPTIONS constant."""

    def test_has_mp3(self):
        """Test that MP3 format exists."""
        values = [opt["value"] for opt in AUDIO_FORMAT_OPTIONS]
        assert "mp3" in values

    def test_has_wav(self):
        """Test that WAV format exists."""
        values = [opt["value"] for opt in AUDIO_FORMAT_OPTIONS]
        assert "wav" in values


class TestSampleRateOptions:
    """Tests for SAMPLE_RATE_OPTIONS constant."""

    def test_values_are_integers(self):
        """Test that sample rate values are integers."""
        for opt in SAMPLE_RATE_OPTIONS:
            assert isinstance(opt["value"], int)

    def test_has_24k(self):
        """Test that 24kHz exists."""
        values = [opt["value"] for opt in SAMPLE_RATE_OPTIONS]
        assert 24000 in values


class TestChannelOptions:
    """Tests for CHANNEL_OPTIONS constant."""

    def test_has_mono(self):
        """Test that mono channel exists."""
        values = [opt["value"] for opt in CHANNEL_OPTIONS]
        assert 1 in values

    def test_has_stereo(self):
        """Test that stereo channel exists."""
        values = [opt["value"] for opt in CHANNEL_OPTIONS]
        assert 2 in values
