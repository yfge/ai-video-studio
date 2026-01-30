---
id: 2025-12-19T22-30-00Z-audio-service-split
date: 2025-12-19T22:30:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [backend, refactor, service-layer, audio, phase2]
related_paths:
  - ai-pic-backend/app/services/audio/__init__.py
  - ai-pic-backend/app/services/audio/audio_generator.py
  - ai-pic-backend/app/services/audio/dialogue_processor.py
  - ai-pic-backend/app/services/audio/timeline_processor.py
  - ai-pic-backend/tests/unit/services/audio/test_audio_generator.py
  - ai-pic-backend/tests/unit/services/audio/test_dialogue_processor.py
  - ai-pic-backend/tests/unit/services/audio/test_timeline_processor.py
summary: "Phase 2.2.1: Split dialogue_audio_service.py into three focused modules"
---

## User Prompt

Continue with Phase 2.2 provider refactoring - split dialogue_audio_service.py (1,261 lines).

## Goals

1. Extract audio file processing utilities to dedicated module
2. Extract dialogue extraction and planning to dedicated module
3. Extract timeline/storyboard generation to dedicated module
4. Create comprehensive unit tests for each module
5. Maintain backward compatibility through package exports

## Changes

### New Files Created

1. **ai-pic-backend/app/services/audio/audio_generator.py** (~180 lines)

   - Low-level audio processing utilities
   - Functions:
     - `ensure_oss_configured()`: Validate OSS service
     - `wav_duration_ms()`: Get WAV file duration
     - `run_ffmpeg()`: Execute ffmpeg commands
     - `generate_silence_wav()`: Create silent WAV
     - `download_to_file()`: Download file from URL
     - `tts_to_wav_file()`: Generate TTS audio
     - `normalize_tts_emotion()`: Map emotion strings to TTS labels
     - `concat_wavs()`, `encode_mp3()`, `concat_mp3s()`: Audio concatenation/encoding

2. **ai-pic-backend/app/services/audio/dialogue_processor.py** (~280 lines)

   - Dialogue extraction and segment planning
   - Classes:
     - `PlannedSegment`: Immutable dataclass for audio segments
   - Functions:
     - `norm_name()`: Normalize character names
     - `looks_like_silence()`: Detect silence/pause text
     - `sanitize_dialogue_content()`: Strip inline stage directions
     - `extract_scene_number()`: Extract scene number from Scene
     - `extract_dialogues_for_scene()`: Get dialogues for scene
     - `extract_stage_for_scene()`: Get stage directions for scene
     - `plan_scene_segments()`: Build ordered segment plan

3. **ai-pic-backend/app/services/audio/timeline_processor.py** (~290 lines)
   - Timeline and storyboard generation
   - Functions:
     - `utc_now_iso()`: Get current UTC timestamp
     - `build_episode_timeline_beats()`: Build timeline from scenes/beats
     - `build_storyboard_frames_from_audio_timeline()`: Generate storyboard frames
     - `_create_frame()`: Create storyboard frame dictionary
     - `generate_storyboard_from_episode_audio_timeline()`: Full storyboard generation with DB persistence

### Modified Files

4. **ai-pic-backend/app/services/audio/**init**.py**
   - Updated to export from all new modules
   - Added comprehensive `__all__` list for public API

### Test Files Created

5. **tests/unit/services/audio/test_audio_generator.py** (~35 tests)

   - Tests for TTS emotion normalization
   - Tests for OSS configuration
   - Tests for WAV/MP3 operations
   - Tests for ffmpeg command execution

6. **tests/unit/services/audio/test_dialogue_processor.py** (~44 tests)

   - Tests for name normalization
   - Tests for silence detection
   - Tests for dialogue sanitization
   - Tests for scene extraction
   - Tests for segment planning

7. **tests/unit/services/audio/test_timeline_processor.py** (~21 tests)
   - Tests for timeline beat building
   - Tests for storyboard frame generation
   - Tests for pause merging logic
   - Tests for storyboard persistence

## Validation

### Import Tests

```bash
python -c "from app.services.audio import PlannedSegment, normalize_tts_emotion, build_episode_timeline_beats; print('OK')"
# Output: OK
```

### Unit Tests

```bash
pytest tests/unit/services/audio/test_audio_generator.py tests/unit/services/audio/test_dialogue_processor.py tests/unit/services/audio/test_timeline_processor.py -v
# Result: 100 passed
```

### Production Build

```bash
./docker/build_prod_images.sh
# Result: SUCCESS - All images built successfully
```

## Architecture Notes

The split follows single responsibility principle:

1. **audio_generator.py**: Low-level audio I/O and TTS

   - Handles ffmpeg, WAV files, MP3 encoding
   - Manages TTS API calls and emotion mapping

2. **dialogue_processor.py**: Script parsing and planning

   - Extracts dialogues/stage directions from scripts
   - Plans audio segments with timing and speaker info

3. **timeline_processor.py**: Timeline construction
   - Builds episode timelines from scene beats
   - Generates storyboard frames from audio timeline

Benefits:

- Each module can be tested independently
- Clear separation of concerns
- Easier to maintain and extend
- Original dialogue_audio_service.py can now delegate to these modules

## Next Steps

1. Update dialogue_audio_service.py to import from new modules (reduce duplication)
2. Phase 2.2.2: Split voice_catalog.py (1,171 lines)
3. Continue provider pattern consolidation

## Linked Commits

- `8bea6b4` - Phase 2.2.1: Split dialogue_audio_service.py into focused modules
