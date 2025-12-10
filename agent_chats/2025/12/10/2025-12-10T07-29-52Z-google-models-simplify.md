---
id: 2025-12-10T07-29-52Z-google-models-simplify
date: 2025-12-10T07:29:52Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, provider]
related_paths:
  - ai-pic-backend/app/services/providers/google_provider.py
summary: "Simplify Google provider model listing to only use the official generativelanguage v1beta models endpoint."
---

## User Prompt

- “google_provider.py 的加载模型的逻辑太乱了，都去掉，只留 https://generativelanguage.googleapis.com/v1beta/models?key=xx 这一个。”

## Goals

- Remove multiple Google model listing fallbacks and only call the official Generative Language models endpoint.
- Keep a minimal, predictable model list flow with static fallback if the call fails.

## Changes

- Rewrote `fetch_remote_models` to call only `https://generativelanguage.googleapis.com/v1beta/models?key=...`, log failures, and fall back to static models.
- Dropped proxy/Vertex/OpenAI-style listing branches; simplified client headers to always use Google API key headers.

## Validation

- Not run (backend services/tests unavailable in this context).

## Next Steps

- When backend env is available, hit `/api/v1/ai/models/available?model_type=text` and confirm Google entries come solely from the v1beta/models response (or fallback when offline).

## Linked Commits

- pending
