---
id: 2026-01-29T10-06-08Z-backend-speech-media-persistence
date: 2026-01-29T10:06:08Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, audio, media, oss]
related_paths:
  - ai-pic-backend/app/services/audio/speech_service.py
  - ai-pic-backend/app/services/ai/speech.py
  - tasks.md
summary: "Refactor speech OSS uploads to use the shared media persistence helper."
---

## User Prompt

- "视频生成后保存上传到 OSS 不是统一的抽象么？"

## Goals

- Reuse the shared media persistence abstraction for audio (TTS) uploads.
- Keep OSS metadata consistent with the video upload path.

## Changes

- Updated `ai-pic-backend/app/services/audio/speech_service.py` to upload audio via `app.services.media` helpers.
- Updated legacy `ai-pic-backend/app/services/ai/speech.py` mixin to reuse the same upload helper (reduces duplication).
- Updated `tasks.md` to reflect progress.

## Validation

- `cd ai-pic-backend && pytest tests/unit/services/audio/test_speech_service.py`
- Docker (local dev stack):
  - Restarted `ai-video-backend`
  - Called `SpeechService._upload_audio_to_oss()` with `https://www.w3schools.com/html/horse.mp3`
  - Verified OSS upload returned `file_url` under `http://resource.lets-gpt.com/ai-generated/audio/...` and metadata includes `provider/model/media_type/voice_type/speed/text`.
- Chrome MCP DevTools check: still failing with `Transport closed`, so browser E2E couldn't be recorded for this commit.

## Next Steps

- Migrate remaining image/audio callsites to the shared media persistence helper (aim: 1 entrypoint for image/video/audio).
- Add `docs/` note for media naming + metadata contract once callsites are unified.

## Linked Commits

- (pending)

