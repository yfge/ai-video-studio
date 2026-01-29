---
id: 2026-01-29T09-50-26Z-backend-media-persistence
date: 2026-01-29T09:50:26Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, media, oss, video]
related_paths:
  - .gitignore
  - ai-pic-backend/app/services/media/media_persistence.py
  - ai-pic-backend/app/services/media/__init__.py
  - ai-pic-backend/app/services/video/video_upload_utils.py
  - ai-pic-backend/tests/unit/services/media/test_media_persistence.py
  - tasks.md
summary: "Introduce shared media persistence helpers for OSS uploads and refactor video upload utils to use them."
---

## User Prompt

- "视频生成后保存上传到 OSS 不是统一的抽象么？"
- "你在 docker 容器中测试一下"

## Goals

- Provide a single backend entrypoint for media uploads (bytes/URL/base64 -> OSS/CDN).
- Refactor storyboard video upload path to reuse the shared persistence helper.
- Validate the end-to-end flow in Docker (generate -> poll -> upload -> storyboard updated).

## Changes

- Added shared helpers in `ai-pic-backend/app/services/media/media_persistence.py`:
  - `upload_from_url`, `upload_bytes`, `upload_base64`
  - `build_generation_metadata` (ASCII-safe OSS metadata contract)
- Added module export in `ai-pic-backend/app/services/media/__init__.py`.
- Refactored `ai-pic-backend/app/services/video/video_upload_utils.py` to call the shared helper and attach consistent metadata (provider/model/duration/fps/resolution).
- Added unit coverage in `ai-pic-backend/tests/unit/services/media/test_media_persistence.py`.

## Validation

- `cd ai-pic-backend && pytest tests/unit tests/services tests/scripts`
- Docker (local dev stack):
  - Restarted `ai-video-backend` and `ai-video-celery-worker`
  - Triggered storyboard video generation: `POST /api/v1/scripts/115/storyboard/generate-video` (frame 10, model `google:veo-3.1-generate-preview`)
  - Verified `video_generation_tasks.result.video_oss_upload.success == true` and `video_url` points to OSS/CDN.
  - Verified storyboard frame 10 has `video_url` updated to the OSS/CDN URL.
- Chrome MCP DevTools check: failed with `Transport closed`, so browser E2E couldn't be recorded for this commit.

## Next Steps

- Refactor speech/audio and image persistence callsites to use the same shared helper (reduce duplication).
- Document media naming + metadata conventions under `docs/` and link from `docs/README.md`.
- Re-run Chrome E2E once MCP DevTools transport is back.

## Linked Commits

- (pending)
