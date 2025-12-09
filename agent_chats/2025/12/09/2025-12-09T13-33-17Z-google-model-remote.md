---
id: 2025-12-09T13-33-17Z-google-model-remote
date: 2025-12-09T13:33:17Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, models]
related_paths:
  - ai-pic-backend/app/services/providers/google_provider.py
summary: "Align Google model listing with OpenAI-compatible and official Gemini endpoints"
---
## User Prompt
参考这个实现google的模型列表加载 

## Goals
- Use Google Gemini model list endpoints (and custom proxy OpenAI-style fallback) rather than only static models.

## Changes
- GoogleProvider now: (1) tries OpenAI-compatible `/v1/models` when using a custom proxy base; (2) calls Vertex AI `v1/models` and Generative Language `v1beta/models?key=...`; (3) dedupes results; (4) still falls back to static Gemini models if remote calls fail.
- Updated client initialization to use Bearer auth for custom base URLs, and `x-goog-api-key` headers for official endpoints.

## Validation
- `python - <<'PY' ... ai_service.list_models(model_type_alias="text", source="remote")` returns providers [deepseek, google, openai, volcengine]; google entries remain 4 (remote calls still 401 with current key).
- Frontend (stories page) already shows Google provider entries; still based on fallback because remote call is unauthorized.

## Next Steps
- Provide a valid Google API key with access to generativelanguage/Vertex AI to get live model lists; rerun `pytest` once credentials are fixed (previous run had pre-existing failures/timeouts).

## Linked Commits
- Pending (will reference after commit)
