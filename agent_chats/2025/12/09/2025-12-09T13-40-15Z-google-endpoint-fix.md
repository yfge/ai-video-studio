---
id: 2025-12-09T13-40-15Z-google-endpoint-fix
date: 2025-12-09T13:40:15Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, models]
related_paths:
  - ai-pic-backend/app/services/providers/google_provider.py
summary: "Adjust Gemini list endpoints and capture failed responses for debugging"
---

## User Prompt

现在docker 中是已经提供google api key 了（希望看到远端模型列表，要求输出原始返回定位问题）

## Goals

- Hit the correct Google Gemini listing endpoints and log raw failures to Docker logs.

## Changes

- Switched Vertex list call to `https://aiplatform.googleapis.com/v1beta1/models` and logged status/url/body when non-2xx.
- Kept Generative Language list on `https://generativelanguage.googleapis.com/v1beta/models`, logging status/url/body on failure; continues to support custom proxy/OpenAI-style `/v1/models`.

## Validation

- `curl` login + `/api/v1/ai/models/available?model_type=text_generation&source=remote` still returns only fallback Google models; Docker logs now show:
  - Vertex list: 404 @ https://aiplatform.googleapis.com/v1beta1/models
  - GLM list: 401 @ https://generativelanguage.googleapis.com/v1beta/models with message “API keys are not supported by this API. Expected OAuth2 access token…”.

## Next Steps

- Provide an AI Studio/Generative Language API key that supports model listing, or supply OAuth access token/service account; once credentials allow 2xx responses, remote models will flow through without falling back.

## Linked Commits

- fix(backend): correct gemini list endpoints and log urls (17c0edc)
