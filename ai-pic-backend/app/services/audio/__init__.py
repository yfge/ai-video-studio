"""
Audio generation service package.

Provides services for AI-powered audio generation including:
- Text-to-speech synthesis
- Audio persistence and OSS upload
- Dialogue processing and planning
- Audio timeline generation
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
]
