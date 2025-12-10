---
id: 2025-12-10T14-30-00Z-image-oss-enforcement
date: 2025-12-10T14:30:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, images, oss]
related_paths:
  - ai-pic-backend/app/services/ai_service.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images.py
summary: "Enforce OSS uploads for all generated virtual IP images/variants and persist OSS URLs to DB."
---

## User Prompt

- “现在所有的图片生成都要上传oss ，并在数据库中保存oss地址”

## Goals

- Make image generation/variants require OSS and store OSS URLs in DB records.
- Centralize OSS uploads for generated images.

## Changes

- Added `_upload_local_image_to_oss` helper in `ai_service` and now require OSS for virtual IP image generation; generation returns `oss_url` and fails on missing/failed uploads.
- `generate_virtual_ip_image` endpoint now errors when OSS is missing and persists returned `oss_url`.
- Variant generation now uploads each variant to OSS with metadata, fails if upload missing, and saves `oss_url` + upload metadata.

## Validation

- `cd ai-pic-backend && pytest tests/unit/test_story_parser.py -q`
- Chrome MCP: not run (backend-only change, no live stack here).

## Next Steps

- Run a live virtual IP image generation/variant flow to confirm OSS URLs are stored and accessible.

## Linked Commits

- pending
