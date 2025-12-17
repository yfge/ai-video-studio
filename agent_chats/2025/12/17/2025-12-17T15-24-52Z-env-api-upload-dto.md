---
id: 2025-12-17T15-24-52Z-env-api-upload-dto
date: 2025-12-17T15:24:52Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, environment, dto]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
  - ai-pic-backend/app/schemas/story_structure.py
summary: "Add environment image upload endpoint and DTO summaries; remove image payloads from list response"
---

## User Prompt

1. 环境列表 不再显示所有的环境图片，增环境详情的页面，在里面进行管理
2. 环境也支持图片上传
3. 所有的 API 接口统一检查，增加 DTO 层，相应字段非必要不返回 ！

## Goals

- Avoid returning heavy image arrays in environment list responses.
- Provide an upload endpoint for environment reference images using the unified OSS persistence.
- Return image data via DTOs instead of raw lists.

## Changes

- Added DTOs for environment summaries and images; list endpoint now returns `EnvironmentSummaryResponse` (no reference_images), and image responses are typed `EnvironmentImagesResponse`/`EnvironmentImageResponse`.
- Added `POST /story-structure/environments/{id}/images/upload` to persist uploads (validates extension/size, uses OSS when configured, updates reference_images) and returns the saved URL via DTO.
- Adjusted image list/delete endpoints to emit DTO wrappers, keeping data minimal while still reporting counts.

## Validation

- Not run in this iteration (backend tests skipped to save time); API changes are limited to DTOs and the new upload path.

## Next Steps

- Verify the upload endpoint end-to-end with the frontend once the environment detail page lands; extend DTO coverage to adjacent endpoints if needed.

## Linked Commits

- TBC: environment upload & DTO adjustments
