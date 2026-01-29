---
id: 2026-01-29T15-09-43Z-backend-image-media-persistence
date: 2026-01-29T15:09:43Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, image, media, oss]
related_paths:
  - ai-pic-backend/app/services/media/media_persistence.py
  - ai-pic-backend/app/services/image/image_persistence.py
  - ai-pic-backend/app/services/ai/images_storage.py
  - ai-pic-backend/app/services/ai_service_manager.py
  - ai-pic-backend/tests/unit/test_ai_service_manager_image_payload_normalization.py
  - tasks.md
summary: "Refactor image persistence and base64 image uploads to reuse shared media persistence helpers."
---

## User Prompt

- "做全流程测试...（后续）"
- "视频生成后保存上传到 OSS 不是统一的抽象么？"
- 选择任务：1（继续 P0-2：统一 image persistence + provider_task_id 长度回归）

## Goals

- Make image upload paths reuse the shared OSS/CDN persistence abstraction (`media_persistence.py`).
- Ensure base64 image payloads are uploaded via the unified helper and carry `sha256` metadata.
- Keep tasks board updated.

## Changes

- Fixed `upload_base64()` in `ai-pic-backend/app/services/media/media_persistence.py` to always attach computed `sha256`.
- Refactored image persistence code to call shared upload helpers:
  - `ai-pic-backend/app/services/image/image_persistence.py`
  - `ai-pic-backend/app/services/ai/images_storage.py`
- Refactored base64 image conversion in `ai-pic-backend/app/services/ai_service_manager.py` to upload via `media_persistence.upload_base64()` with standardized metadata.
- Added/updated unit coverage in `ai-pic-backend/tests/unit/test_ai_service_manager_image_payload_normalization.py` to prevent real OSS uploads during tests.
- Updated `tasks.md` to mark image/video/audio unified persistence item complete.

## Validation

- Unit tests:
  - `cd ai-pic-backend && pytest tests/unit/services/media/test_media_persistence.py`
  - `cd ai-pic-backend && pytest tests/unit/services/image/test_image_persistence.py`
  - `cd ai-pic-backend && pytest tests/unit/test_ai_service_manager_image_payload_normalization.py`
- Docker sanity check (local dev stack):
  - `docker exec ai-video-backend` and called `ImageStorageMixin._persist_generated_image()` with an existing storyboard image URL
  - Verified returned `oss_url` and `oss_upload.metadata.sha256/generated_at` are present and consistent.
- Chrome MCP DevTools: still unavailable (`Transport closed`), so no browser E2E recording for this commit.

## Next Steps

- Implement the remaining part of option (1): provider_task_id length regression + migration safety (MySQL 1406 avoidance).

## Linked Commits

- (pending)

