---
id: 2025-12-19T23-00-00Z-voice-catalog-reorganize
date: 2025-12-19T23:00:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [backend, refactor, audio, voice, phase2]
related_paths:
  - ai-pic-backend/app/services/audio/voice_catalog.py
  - ai-pic-backend/app/services/audio/voice_constants.py
  - ai-pic-backend/app/services/audio/__init__.py
  - ai-pic-backend/tests/unit/services/audio/test_voice_catalog.py
summary: "Phase 2.2.2: Reorganize voice_catalog.py into audio module"
---

## User Prompt

Continue with Phase 2.2.2 - reorganize voice_catalog.py.

## Goals

1. Move voice catalog data to the audio service module
2. Extract voice option constants for reuse
3. Create comprehensive unit tests
4. Maintain backward compatibility

## Analysis

The original refactoring plan suggested splitting voice_catalog.py (1,171 lines) into:

- voice_repository.py
- voice_selector.py
- voice_cache.py

However, examination revealed that voice_catalog.py is **pure static data** - a single
list constant `SYSTEM_VOICE_CATALOG` with 327 voice definitions. No logic to split.

The practical approach was to:

1. Move the data file to the audio module
2. Extract voice configuration constants from voice_service.py

## Changes

### New Files Created

1. **ai-pic-backend/app/services/audio/voice_catalog.py** (~1,171 lines)

   - Moved from `app/services/voice_catalog.py`
   - Contains `SYSTEM_VOICE_CATALOG` - 327 system voice definitions
   - Voice data for MiniMax TTS with language tags

2. **ai-pic-backend/app/services/audio/voice_constants.py** (~120 lines)
   - Extracted from voice_service.py
   - Constants:
     - `DEFAULT_MINIMAX_VOICE_ID`
     - `VOICE_TYPE_OPTIONS`
     - `TTS_MODEL_OPTIONS`
     - `EMOTION_OPTIONS`
     - `LANGUAGE_BOOST_OPTIONS`
     - `OUTPUT_FORMAT_OPTIONS`
     - `AUDIO_FORMAT_OPTIONS`
     - `SAMPLE_RATE_OPTIONS`
     - `BITRATE_OPTIONS`
     - `CHANNEL_OPTIONS`
     - `MUSIC_MODEL_OPTIONS`

### Modified Files

3. **ai-pic-backend/app/services/audio/**init**.py**
   - Added exports for voice_catalog and voice_constants

### Test Files Created

4. **tests/unit/services/audio/test_voice_catalog.py** (~33 tests)
   - Tests for SYSTEM_VOICE_CATALOG structure and uniqueness
   - Tests for all option constants
   - Tests for default voice ID existence

## Validation

### Import Tests

```bash
python -c "from app.services.audio import SYSTEM_VOICE_CATALOG, DEFAULT_MINIMAX_VOICE_ID; print('OK')"
# Output: OK
```

### Unit Tests

```bash
pytest tests/unit/services/audio/test_voice_catalog.py -v
# Result: 33 passed
```

### Production Build

```bash
./docker/build_prod_images.sh
# Result: SUCCESS
```

## Architecture Notes

The voice module reorganization consolidates audio-related resources:

1. **voice_catalog.py**: Static voice data (327 voices across multiple languages)

   - Chinese (zh-CN, zh-HK)
   - English (en)
   - Japanese (ja)
   - Korean (ko)
   - Spanish (es)
   - Portuguese (pt)
   - And more...

2. **voice_constants.py**: UI configuration options
   - Voice types: system, cloning, generation
   - TTS models: speech-2.6-hd, speech-2.6-turbo, etc.
   - Emotions: happy, sad, angry, calm, etc.
   - Audio quality settings

Benefits:

- All audio/voice resources in one module
- Constants can be imported from audio package
- Original voice_catalog.py preserved for backward compatibility

## Next Steps

1. Update voice_service.py to import from audio module (reduce duplication)
2. Continue with next refactoring phase
3. Consider deprecating original voice_catalog.py location

## Linked Commits

- `b58ffe3` - Phase 2.2.2: Reorganize voice catalog into audio module
