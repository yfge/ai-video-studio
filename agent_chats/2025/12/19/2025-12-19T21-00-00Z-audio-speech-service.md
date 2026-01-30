---
id: 2025-12-19T21-00-00Z-audio-speech-service
date: 2025-12-19T21:00:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [backend, refactor, service-layer, audio, speech, phase2]
related_paths:
  - ai-pic-backend/app/services/audio/__init__.py
  - ai-pic-backend/app/services/audio/speech_service.py
  - ai-pic-backend/app/services/audio/text_generation_utils.py
  - ai-pic-backend/tests/unit/services/audio/test_speech_service.py
  - ai-pic-backend/tests/unit/services/audio/test_text_generation_utils.py
summary: "Phase 2.1.3: Extract Audio/Speech Service from monolithic ai_service.py"
---

## User Prompt

Continue with Phase 2.1.3 of the refactoring plan - create Text/Audio Generation Service.

## Goals

1. Create a dedicated Audio/Speech Service module
2. Extract speech synthesis functionality from ai_service.py
3. Create text generation utilities for shared use
4. Create comprehensive unit tests
5. Ensure production build passes

## Changes

### New Files Created

1. **ai-pic-backend/app/services/audio/**init**.py** (~13 lines)

   - Package initialization
   - Exports: `SpeechService`, `get_speech_service`

2. **ai-pic-backend/app/services/audio/speech_service.py** (~165 lines)

   - `SpeechService`: Service class for AI-powered text-to-speech synthesis
   - Methods:
     - `generate_speech()`: Main TTS generation entry point
     - `_process_successful_response()`: Response processing with OSS upload
     - `_upload_audio_to_oss()`: Audio OSS upload with metadata
     - `_get_oss_url_or_original()`: URL selection helper
   - Factory function: `get_speech_service()`

3. **ai-pic-backend/app/services/audio/text_generation_utils.py** (~90 lines)
   - Utility functions for text generation
   - Functions:
     - `call_text_generation_with_fallback()`: Service fallback pattern
     - `trim_text()`: Text truncation with ellipsis
     - `extract_text_content()`: Extract text from various response formats

### Test Files Created

4. **tests/unit/services/audio/test_speech_service.py** (~17 tests)

   - Tests for `SpeechService` class
   - Tests for generation success/failure scenarios
   - Tests for OSS upload methods
   - Tests for text truncation in metadata

5. **tests/unit/services/audio/test_text_generation_utils.py** (~22 tests)
   - Tests for `call_text_generation_with_fallback()`
   - Tests for `trim_text()` edge cases
   - Tests for `extract_text_content()` with various formats

## Validation

### Import Tests

```bash
python -c "from app.services.audio import SpeechService, get_speech_service; print('Speech Service import OK')"
# Output: Speech Service import OK
```

### Unit Tests

```bash
pytest tests/unit/services/audio/ -v
# Result: 39 passed (100%)
```

### Production Build

```bash
./docker/build_prod_images.sh
# Result: SUCCESS - All images built successfully
```

## Architecture Notes

The Audio Service follows the established pattern:

1. **Service Layer** (`speech_service.py`)

   - Text-to-speech generation orchestration
   - Response processing with OSS upload
   - Provider preference support

2. **Utilities** (`text_generation_utils.py`)
   - Reusable text utilities
   - Service fallback pattern
   - Response content extraction

Key features:

- Text truncation in OSS metadata to avoid excessive sizes
- Multi-provider support via ai_manager
- Consistent response format matching other services

## Next Steps

1. Phase 2.1.4: Refactor AIService to Coordinator
2. Integrate all extracted services as delegates
3. Update endpoints to use new services

## Linked Commits

- `e0041d9` - Phase 2.1.3: Audio/Speech Service extraction
