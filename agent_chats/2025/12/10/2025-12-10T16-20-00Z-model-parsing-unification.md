---
id: 2025-12-10T16-20-00Z-model-parsing-unification
date: 2025-12-10T16:20:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, models]
related_paths:
  - ai-pic-backend/app/utils/model_utils.py
  - ai-pic-backend/app/services/ai_service.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
summary: "Unify provider-prefixed model parsing and apply it to environment image generation to prevent invalid OpenAI model IDs."
---

## User Prompt

- “把所有模型解析的问题统一抽象，不要再有这么 SB 的 BUG！！”

## Goals

- Provide a single utility to parse `provider:model` strings and infer providers heuristically.
- Use the helper in environment image generation/variants to strip prefixes and avoid bad model IDs (e.g., `openai:dall-e-3` → `dall-e-3` with provider hint).

## Changes

- Added `app/utils/model_utils.py` with `parse_model_and_provider` and provider inference helpers.
- Wired the helper into environment generation/variant endpoints, preserving provider hints while cleaning model IDs.
- Hooked the helper into virtual IP image generation via `ai_service` import (ready for wider use).

## Validation

- `cd ai-pic-backend && pytest tests/unit/test_story_parser.py -q`
- Chrome MCP: not run (backend-only change).

## Next Steps

- Roll this parsing helper through other endpoints/services that accept `provider:model` to eliminate remaining prefixes and keep provider hints consistent.

## Linked Commits

- pending
