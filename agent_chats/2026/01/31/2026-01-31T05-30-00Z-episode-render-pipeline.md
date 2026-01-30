---
id: 2026-01-31T05-30-00Z-episode-render-pipeline
date: 2026-01-31T05:30:00Z
participants: [human, claude]
models: [claude-opus-4-5-20251101]
tags: [backend, render, video, ffmpeg]
related_paths:
  - ai-pic-backend/app/services/render/__init__.py
  - ai-pic-backend/app/services/render/video_concat.py
  - ai-pic-backend/app/services/render/episode_render_service.py
  - ai-pic-backend/tests/unit/services/render/__init__.py
  - ai-pic-backend/tests/unit/services/render/test_video_concat.py
  - ai-pic-backend/tests/unit/services/render/test_episode_render_service.py
summary: "Implemented episode render pipeline with FFmpeg video concat and audio replacement"
---

## User Prompt

Continue work on episode133-render-mp4 task - upgrade "concat + audio replace" to formal render pipeline.

## Goals

1. Create dedicated `app/services/render/` module for episode video rendering
2. Implement FFmpeg-based video concatenation utilities
3. Create EpisodeRenderService for coordinating frame-to-video-to-concat workflow
4. Write comprehensive unit tests
5. Fix import errors and deprecation warnings

## Changes

### New Files Created

1. **`app/services/render/__init__.py`** - Module exports for render services
2. **`app/services/render/video_concat.py`** (285 lines) - FFmpeg utilities:
   - `VideoClip` dataclass for clip metadata
   - `download_all_clips()` - async video download
   - `trim_clip_to_duration()` - trim/pad clips to target duration
   - `create_concat_file()` - FFmpeg concat demuxer file creation
   - `concat_videos_ffmpeg()` - concatenate videos with optional audio
   - `replace_audio()` - replace video audio track
   - `concat_video_clips()` - main async function orchestrating the pipeline

3. **`app/services/render/episode_render_service.py`** (229 lines) - Service class:
   - `get_storyboard_clips()` - extract VideoClip list from script storyboard
   - `get_episode_audio_url()` - get TTS dialogue audio URL
   - `render_episode()` - main render method (video_audio + tts_audio versions)
   - `_render_version()` - render single version with OSS upload
   - `_save_render_results()` - persist results to episode metadata

4. **`tests/unit/services/render/test_video_concat.py`** (221 lines) - Unit tests:
   - TestVideoClip (2 tests)
   - TestCreateConcatFile (2 tests)
   - TestTrimClipToDuration (2 tests)
   - TestConcatVideosFFmpeg (2 tests)
   - TestReplaceAudio (2 tests)

5. **`tests/unit/services/render/test_episode_render_service.py`** (286 lines) - Unit tests:
   - TestGetStoryboardClips (5 tests)
   - TestGetEpisodeAudioUrl (3 tests)
   - TestRenderEpisode (4 tests)
   - TestSaveRenderResults (1 test)

### Fixes Applied

- Fixed import error: Changed `from app.services.media.media_persistence import MediaPersistence, MediaType` to `from app.services.media import upload_bytes`
- Fixed method calls: Changed `self.media_persistence.upload_bytes()` to module function `upload_bytes()`
- Fixed parameter mapping: Adapted to `upload_bytes(content=, filename=, media_type=, prefix=, metadata=)` signature
- Fixed deprecation: Changed `datetime.utcnow()` to `datetime.now(timezone.utc)`

## Validation

```bash
python -m pytest tests/unit/services/render/ -v
# Result: 23 passed tests

python -c "from app.services.render import EpisodeRenderService; print('Import OK')"
# Result: Import OK
```

All 23 unit tests pass covering:
- VideoClip dataclass creation
- Concat file creation with path escaping
- Clip trimming/padding logic
- FFmpeg concatenation with/without audio
- Audio replacement
- Storyboard clip extraction
- Episode audio URL extraction
- Render workflow error handling
- Result persistence

## Next Steps

1. Create API endpoint `POST /api/v1/episodes/{id}/render` to expose render service
2. Integrate render pipeline with existing storyboard video generation workflow
3. Add Celery task for background rendering
4. Implement progress callbacks for long-running renders
5. Work on remaining today's items:
   - video-duration-alignment: Phase 1 capabilities registry

## Linked Commits

(To be committed)
