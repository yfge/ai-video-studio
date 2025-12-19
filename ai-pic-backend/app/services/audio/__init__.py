"""
Audio generation service package.

Provides services for AI-powered audio generation including:
- Text-to-speech synthesis
- Audio persistence and OSS upload
- Dialogue processing and planning
- Audio timeline generation
- Voice catalog and configuration constants
"""

from app.services.audio.speech_service import (
    SpeechService,
    get_speech_service,
)
from app.services.audio.audio_generator import (
    ALLOWED_TTS_EMOTIONS,
    wav_duration_ms,
    generate_silence_wav,
    tts_to_wav_file,
    normalize_tts_emotion,
    concat_wavs,
    encode_mp3,
    concat_mp3s,
)
from app.services.audio.dialogue_processor import (
    PlannedSegment,
    norm_name,
    looks_like_silence,
    sanitize_dialogue_content,
    extract_scene_number,
    extract_dialogues_for_scene,
    extract_stage_for_scene,
    plan_scene_segments,
)
from app.services.audio.timeline_processor import (
    utc_now_iso,
    build_episode_timeline_beats,
    build_storyboard_frames_from_audio_timeline,
    generate_storyboard_from_episode_audio_timeline,
)
from app.services.audio.voice_catalog import SYSTEM_VOICE_CATALOG
from app.services.audio.voice_constants import (
    DEFAULT_MINIMAX_VOICE_ID,
    VOICE_TYPE_OPTIONS,
    TTS_MODEL_OPTIONS,
    EMOTION_OPTIONS,
    LANGUAGE_BOOST_OPTIONS,
    OUTPUT_FORMAT_OPTIONS,
    AUDIO_FORMAT_OPTIONS,
    SAMPLE_RATE_OPTIONS,
    BITRATE_OPTIONS,
    CHANNEL_OPTIONS,
    MUSIC_MODEL_OPTIONS,
)

__all__ = [
    # Speech service
    "SpeechService",
    "get_speech_service",
    # Audio generator utilities
    "ALLOWED_TTS_EMOTIONS",
    "wav_duration_ms",
    "generate_silence_wav",
    "tts_to_wav_file",
    "normalize_tts_emotion",
    "concat_wavs",
    "encode_mp3",
    "concat_mp3s",
    # Dialogue processor
    "PlannedSegment",
    "norm_name",
    "looks_like_silence",
    "sanitize_dialogue_content",
    "extract_scene_number",
    "extract_dialogues_for_scene",
    "extract_stage_for_scene",
    "plan_scene_segments",
    # Timeline processor
    "utc_now_iso",
    "build_episode_timeline_beats",
    "build_storyboard_frames_from_audio_timeline",
    "generate_storyboard_from_episode_audio_timeline",
    # Voice catalog and constants
    "SYSTEM_VOICE_CATALOG",
    "DEFAULT_MINIMAX_VOICE_ID",
    "VOICE_TYPE_OPTIONS",
    "TTS_MODEL_OPTIONS",
    "EMOTION_OPTIONS",
    "LANGUAGE_BOOST_OPTIONS",
    "OUTPUT_FORMAT_OPTIONS",
    "AUDIO_FORMAT_OPTIONS",
    "SAMPLE_RATE_OPTIONS",
    "BITRATE_OPTIONS",
    "CHANNEL_OPTIONS",
    "MUSIC_MODEL_OPTIONS",
]
