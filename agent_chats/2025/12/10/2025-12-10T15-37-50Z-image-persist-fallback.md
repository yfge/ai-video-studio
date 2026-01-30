---
id: 2025-12-10T15-37-50Z-image-persist-fallback
date: 2025-12-10T15:37:50Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, image, oss]
related_paths:
  - ai-pic-backend/app/services/ai_service.py
summary: "Relax image persistence so non-critical callers can fall back to local paths when OSS upload fails instead of returning empty image lists."
---

## User Prompt

- 用户指出环境图接口返回 `images: []`，而环境列表中 `reference_images` 仍然只有老的 `/uploads/...`，质疑 OSS 抽象是否真正生效。

## Goals

- Avoid swallowing OSS upload failures in a way that causes environment image generation to return an empty `images` array while the LLM call itself succeeded.
- Let callers that don't require OSS (e.g., environment references) still persist local images even if OSS upload fails.

## Changes

- Updated `AIService._persist_generated_image` so that:
  - `oss_service.upload_file_content` is wrapped in a `try/except`.
  - When `require_upload` is `False`, OSS failures now emit a warning and fall back to local `/uploads/...` paths instead of raising.
  - When `require_upload` is `True`, behavior is unchanged: OSS failures still raise and propagate.

## Validation

- `cd ai-pic-backend && pytest tests/unit/test_model_utils.py tests/unit/test_base_provider_client.py -q`
- Docker logs show environment image generation calling `_download_image` and OSS uploader; future calls should no longer end up with `images: []` due solely to OSS issues.

## Next Steps

- Add targeted tests to assert that `_persist_generated_image` returns a non-empty `relative_path` even when OSS upload fails and `require_upload=False`.

## Linked Commits

- pending
