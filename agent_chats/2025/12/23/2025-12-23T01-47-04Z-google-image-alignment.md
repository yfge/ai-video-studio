---
id: 2025-12-23T01-47-04Z-google-image-alignment
date: 2025-12-23T01:47:04Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, provider]
related_paths:
  - ai-pic-backend/app/services/providers/google_provider/image.py
  - ai-pic-backend/app/services/providers/google_provider/models.py
  - ai-pic-backend/app/services/providers/google_provider/provider.py
  - ai-pic-backend/app/services/providers/image_param_utils.py
summary: "Aligned Google image generation params with docs"
---

## User Prompt

- Align Google model calls with docs/api/google.

## Goals

- Match Google image generation parameter support (aspect ratios and sizes) to the documented API.
- Ensure UI metadata for Google models reflects supported ratios/sizes.
- Avoid sending unsupported image_size for non-Pro Gemini models.

## Changes

- Expanded Google aspect ratio list and added Gemini 3 Pro size options in shared image UI rules.
- Updated Google image model metadata to expose new aspect ratios and 1K/2K/4K sizes for Gemini 3 Pro.
- Enriched remote Google model listings with UI metadata and suppressed image_size when unsupported.

## Validation

- pytest (ai-pic-backend): TIMED OUT at 120s; multiple existing failures across diagnostic/user management/keling/api/migrations/models suites.
- ./docker/build_prod_images.sh: PASS.
- MCP Chrome E2E: Environment detail page -> Google model shows expanded 画幅比例 list (含 21:9); selecting Gemini 3 Pro Image Preview shows 分辨率/尺寸 with 1K/2K/4K.

## Next Steps

- Verify actual Gemini image generation with 3 Pro size options in task execution logs.
- Revisit baseline pytest failures to unblock clean CI runs.

## Linked Commits

- TBD
