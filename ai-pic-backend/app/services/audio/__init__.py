"""
Audio generation service package.

Provides services for AI-powered audio generation including:
- Text-to-speech synthesis
- Audio persistence and OSS upload
- Dialogue processing and planning
- Audio timeline generation
- Voice catalog and configuration constants
"""

from app.services.audio.audio_emotions import (
    ALLOWED_TTS_EMOTIONS,
    normalize_tts_emotion,
)
from app.services.audio.audio_generator import (
    concat_mp3s,
    concat_wavs,
    encode_mp3,
    generate_silence_wav,
    tts_to_wav_file,
    wav_duration_ms,
)
from app.services.audio.dialogue_processor import (
    PlannedSegment,
    extract_dialogues_for_scene,
    extract_scene_number,
    extract_stage_for_scene,
    looks_like_silence,
    norm_name,
    plan_scene_segments,
    sanitize_dialogue_content,
)
from app.services.audio.episode_timeline_beats import build_episode_timeline_beats
from app.services.audio.speech_service import SpeechService, get_speech_service
from app.services.audio.storyboard_from_timeline import (
    build_storyboard_frames_from_audio_timeline,
    generate_storyboard_from_episode_audio_timeline,
)
from app.services.audio.storyboard_from_timeline_spec import (
    build_storyboard_frames_from_timeline_spec,
    generate_storyboard_support_from_timeline_spec,
)
from app.services.audio.voice_constants import (
    AUDIO_FORMAT_OPTIONS,
    BITRATE_OPTIONS,
    CHANNEL_OPTIONS,
    DEFAULT_MINIMAX_VOICE_ID,
    EMOTION_OPTIONS,
    LANGUAGE_BOOST_OPTIONS,
    MUSIC_MODEL_OPTIONS,
    OUTPUT_FORMAT_OPTIONS,
    SAMPLE_RATE_OPTIONS,
    TTS_MODEL_OPTIONS,
    VOICE_TYPE_OPTIONS,
)
from app.services.voice_catalog import SYSTEM_VOICE_CATALOG

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
    "build_episode_timeline_beats",
    "build_storyboard_frames_from_audio_timeline",
    "build_storyboard_frames_from_timeline_spec",
    "generate_storyboard_from_episode_audio_timeline",
    "generate_storyboard_support_from_timeline_spec",
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
