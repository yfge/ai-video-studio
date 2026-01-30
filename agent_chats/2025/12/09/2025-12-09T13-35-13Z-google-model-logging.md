---
id: 2025-12-09T13-35-13Z-google-model-logging
date: 2025-12-09T13:35:13Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, observability]
related_paths:
  - ai-pic-backend/app/services/providers/google_provider.py
summary: "Add logging for Google model list fetch failures"
---

## User Prompt

还是不对，你在日志中输出原始返回自己docker logs 排查一下

## Goals

- Surface Google model list fetch failures (Vertex/Generative Language/custom proxy) in logs to aid debugging.

## Changes

- GoogleProvider now logs status code and trimmed response body when model list calls return non-2xx for proxy `/v1/models`, Vertex `v1/models`, and Generative Language `v1beta/models`.

## Validation

- Not run (logging-only change; previous manual run still shows 401 for current GOOGLE_API_KEY).

## Next Steps

- Use a valid Google API key to get successful responses; inspect logs if errors persist.

## Linked Commits

- Pending (will reference after commit)
