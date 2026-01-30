---
id: 2025-12-09T09-28-43Z-openai-structured
date: 2025-12-09T09:28:43Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, ai-models]
related_paths:
  - ai-pic-backend/app/services/providers/openai_provider.py
summary: "Align OpenAI payload with structured outputs per model"
---

## User Prompt

openai 不同的模型参数是有区别的，对齐这些参数 https://platform.openai.com/docs/guides/structured-outputs。

## Goals

- Use structured outputs (response_format.json_schema + strict) for models that support it.
- Keep compatibility for older models with json_object fallback.

## Changes

- Added helper to detect structured-output capable models (gpt-4.1*, gpt-4o*, gpt-4o-mini*, gpt-4o-audio*, gpt-4o-realtime*, o3*, o1\*).
- In `generate_text`, when `json_schema` is provided and the model supports structured outputs, send `response_format` with `type=json_schema`, `strict=True`, and provided schema; otherwise fallback to `response_format: json_object`. Retains temperature/reasoning tweaks via `_reload_openai_params`.

## Validation

- `pytest tests/test_ai_service.py -q`

## Next Steps

- Consider mapping additional model-specific params (e.g., reasoning_effort) as product docs evolve.

## Linked Commits

- (this commit)
