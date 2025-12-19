---
id: 2025-12-19T11-45-00Z-refactor-minimax-provider
date: 2025-12-19T11:45:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [backend, refactor, providers, phase4]
related_paths:
  - ai-pic-backend/app/services/providers/minimax_provider/__init__.py
  - ai-pic-backend/app/services/providers/minimax_provider/provider.py
  - ai-pic-backend/app/services/providers/minimax_provider/models.py
  - ai-pic-backend/app/services/providers/minimax_provider/text.py
  - ai-pic-backend/app/services/providers/minimax_provider/tts.py
  - ai-pic-backend/app/services/providers/minimax_provider/video.py
summary: "Refactored minimax_provider.py (678 lines) into modular package structure [Phase 4.5]"
---

## User Prompt

Continue with Phase 4 provider refactoring (from context continuation).

## Goals

1. Split minimax_provider.py (678 lines) into smaller focused modules
2. Maintain all existing functionality for text generation, TTS, and video generation
3. Keep imports working without changes to dependent code
4. Verify production build passes

## Changes

### Created minimax_provider package structure:

1. **`__init__.py`** (9 lines)
   - Package exports: `MinimaxProvider`

2. **`models.py`** (230 lines)
   - Text generation models: abab6.5s-chat, abab6.5-chat, abab6.5g-chat
   - TTS models: speech-2.6-hd, speech-2.6-turbo, speech-02-hd, speech-02-turbo, speech-01-hd, speech-01-turbo
   - Video models: Hailuo 2.3, Hailuo 2.3 Fast, Hailuo 0.2, I2V-01-Director, I2V-01-live, I2V-01

3. **`provider.py`** (173 lines)
   - Main `MinimaxProvider` class
   - Client initialization with MinimaxClient
   - Delegates to text, tts, and video modules

4. **`text.py`** (68 lines)
   - Text generation: `generate_text`

5. **`tts.py`** (134 lines)
   - Text-to-speech: `text_to_speech`
   - Voice listing: `get_voices`
   - Helper: `_to_int` for parameter conversion

6. **`video.py`** (200 lines)
   - Video generation: `generate_video`
   - Task polling: `_poll_video_task`
   - File retrieval: `_retrieve_video_file`

### Deleted:
- `ai-pic-backend/app/services/providers/minimax_provider.py` (original 678 line monolith)

### Import compatibility:
- Package `__init__.py` exports `MinimaxProvider`, maintaining API compatibility
- No changes needed to `ai_service_manager.py` or `providers/__init__.py`

## Validation

1. Import test passed: `python -c "from app.services.providers.minimax_provider import MinimaxProvider"`
2. Production build `./docker/build_prod_images.sh` - PASSED

## Next Steps

Phase 4 provider refactoring complete. All 5 large providers have been modularized:
- volcengine_provider (1,409 lines -> package)
- keling_provider (843 lines -> package)
- openai_provider (774 lines -> package)
- google_provider (760 lines -> package)
- minimax_provider (678 lines -> package)

## Linked Commits

- 16c0523 refactor(backend): split minimax_provider.py into modular package [phase4.5]
