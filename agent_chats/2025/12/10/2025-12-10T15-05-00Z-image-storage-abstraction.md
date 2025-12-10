---
id: 2025-12-10T15-05-00Z-image-storage-abstraction
date: 2025-12-10T15:05:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, images, oss]
related_paths:
  - ai-pic-backend/app/services/ai_service.py
  - ai-pic-backend/app/api/v1/endpoints/virtual_ip_images.py
summary: "Refactor image persistence to a shared helper that uploads to OSS when available and records OSS URLs."
---

## User Prompt

- “现在 IP ，场景，分镜，都有文生图，图生图，这些调用的抽象是一致的么”
- “那现在开始做这些，这同时如果配置 OSS 就走 OSS，否则 就走本地，做好这一展抽象，提示的拼装可以在各自场景内部走，但是这一层要有公共的抽象”

## Goals

- Centralize generated-image persistence with optional OSS upload and shared metadata handling.
- Ensure virtual IP image generation/variants store OSS URLs when configured, otherwise keep local paths.

## Changes

- Added `_persist_generated_image` helper in `ai_service` that downloads (URL/base64) to local, gathers file info, and uploads to OSS if configured; returns relative path and OSS info.
- Virtual IP generation now uses this helper (no longer hard-requires OSS), returning both relative path and OSS URL.
- Variant generation uploads via the shared helper when OSS is present and records OSS metadata; gracefully falls back to local paths when OSS is absent.

## Validation

- `cd ai-pic-backend && pytest tests/unit/test_story_parser.py -q`
- Chrome MCP: not run (backend-only change, no live stack here).

## Next Steps

- Extend the shared image persistence helper to scene/storyboard image outputs so all image flows align.
- Run live image generation/variant flows to confirm OSS URLs persist correctly and local fallback works when OSS is disabled.

## Linked Commits

- pending
