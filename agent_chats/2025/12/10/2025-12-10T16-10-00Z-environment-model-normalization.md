---
id: 2025-12-10T16-10-00Z-environment-model-normalization
date: 2025-12-10T16:10:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, models, image]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
summary: "Normalize provider-prefixed model ids for environment image/variant generation to prevent OpenAI 400s."
---

## User Prompt

- Provided a 400 from OpenAI images: `'openai:dall-e-3'` rejected by `/api/v1/story-structure/environments/{id}/images/generate`.

## Goals

- Strip provider prefixes before calling `ai_manager.generate_image/image_to_image` in environment endpoints to avoid invalid OpenAI model ids.

## Changes

- Added `_strip_provider_prefix` helper and applied it to environment image generation and variants; model selection now passes `dall-e-3` instead of `openai:dall-e-3` while keeping provider hints.

## Validation

- `cd ai-pic-backend && pytest tests/unit/test_story_parser.py -q`
- Chrome MCP: not run (backend-only change).

## Next Steps

- Run the environment image generation endpoint with `openai:dall-e-3` to confirm 200 and stored URLs; consider adding similar normalization to any remaining endpoints that accept provider-prefixed model ids.

## Linked Commits

- pending
