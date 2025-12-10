---
id: 2025-12-10T15-11-29Z-openai-style-normalization
date: 2025-12-10T15:11:29Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, models, image]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
  - ai-pic-backend/app/utils/model_utils.py
  - ai-pic-backend/tests/unit/test_model_utils.py
summary: "Normalize OpenAI image style handling and provider hints in environment image endpoints to avoid invalid model/style errors."
---

## User Prompt

- “| For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400 ... Invalid value: 'openai:dall-e-3'. Supported values are: 'gpt-image-1', 'gpt-image-1-mini', 'dall-e-2', and 'dall-e-3'.”

## Goals

- Ensure environment image generation/variants strip provider prefixes and send OpenAI-compliant style values.
- Add coverage for model parsing and style normalization helpers.

## Changes

- Normalized `style` for OpenAI providers in environment generate/variant endpoints and propagated provider hints safely.
- Added `normalize_openai_image_style` helper alongside model parsing utilities.
- Added unit tests covering model parsing and style normalization behavior.

## Validation

- `cd ai-pic-backend && pytest tests/unit/test_model_utils.py -q`
- Chrome MCP: not run (backend-only change; service not running here).

## Next Steps

- Extend the normalization helper to any remaining image endpoints that pass arbitrary style strings.

## Linked Commits

- pending
