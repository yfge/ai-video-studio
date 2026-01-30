---
id: 2025-12-19T20-30-00Z-video-generation-service
date: 2025-12-19T20:30:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [backend, refactor, service-layer, video-generation, phase2]
related_paths:
  - ai-pic-backend/app/services/video/__init__.py
  - ai-pic-backend/app/services/video/video_generation_service.py
  - ai-pic-backend/app/services/video/video_ui_utils.py
  - ai-pic-backend/tests/unit/services/video/test_video_generation_service.py
  - ai-pic-backend/tests/unit/services/video/test_video_ui_utils.py
summary: "Phase 2.1.2: Extract Video Generation Service from monolithic ai_service.py"
---

## User Prompt

Continue with Phase 2.1.2 of the refactoring plan - create Video Generation Service.

## Goals

1. Create a dedicated Video Generation Service module
2. Extract video-related functionality from ai_service.py
3. Create video UI utilities for provider capability computation
4. Create comprehensive unit tests
5. Ensure production build passes

## Changes

### New Files Created

1. **ai-pic-backend/app/services/video/**init**.py** (~15 lines)

   - Package initialization
   - Exports: `VideoGenerationService`, `get_video_generation_service`

2. **ai-pic-backend/app/services/video/video_generation_service.py** (~240 lines)

   - `VideoGenerationService`: Main service class for AI-powered video generation
   - Methods:
     - `generate_video()`: Main generation entry point (text-to-video or image-to-video)
     - `_process_successful_response()`: Process response with OSS uploads
     - `_upload_video_to_oss()`: Video OSS upload with metadata
     - `_upload_thumbnail_to_oss()`: Thumbnail OSS upload
     - `_upload_last_frame_to_oss()`: Last frame OSS upload
     - `_get_oss_url_or_original()`: URL selection helper
   - Factory function: `get_video_generation_service()`

3. **ai-pic-backend/app/services/video/video_ui_utils.py** (~185 lines)
   - UI utility functions for video model capability computation
   - Functions:
     - `compute_video_ui()`: Compute video UI options from capabilities
     - `compute_image_ui()`: Compute image UI options (shared utility)
     - `_apply_keling_defaults()`: Keling provider defaults
     - `_apply_volcengine_defaults()`: Volcengine provider defaults
     - `_apply_minimax_defaults()`: MiniMax provider defaults

### Test Files Created

4. **tests/unit/services/video/test_video_generation_service.py** (~19 tests)

   - Tests for `VideoGenerationService` class
   - Tests for generation success/failure scenarios
   - Tests for OSS upload methods

5. **tests/unit/services/video/test_video_ui_utils.py** (~18 tests)
   - Tests for `compute_video_ui()` function
   - Tests for `compute_image_ui()` function
   - Tests for provider-specific defaults

## Validation

### Import Tests

```bash
python -c "from app.services.video import VideoGenerationService, get_video_generation_service; print('Video Service import OK')"
# Output: Video Service import OK
```

### Unit Tests

```bash
pytest tests/unit/services/video/ -v
# Result: 37 passed (100%)
```

### Production Build

```bash
./docker/build_prod_images.sh
# Result: SUCCESS - All images built successfully
```

## Architecture Notes

The Video Generation Service follows the same pattern as Image Generation Service:

1. **Service Layer** (`video_generation_service.py`)

   - Main generation orchestration
   - Response processing
   - OSS upload coordination

2. **UI Utilities** (`video_ui_utils.py`)
   - Provider capability parsing
   - UI options computation
   - Provider-specific defaults

Key features:

- Automatic last frame return for video chaining
- OSS upload for video, thumbnail, and last frame
- Provider-specific capability detection (Keling, Volcengine, MiniMax)

## Next Steps

1. Phase 2.1.3: Create Text Generation Service (speech synthesis)
2. Phase 2.1.4: Refactor AIService to Coordinator
3. Integrate extracted services as delegates

## Linked Commits

- `f388d85` - Phase 2.1.2: Video Generation Service extraction
