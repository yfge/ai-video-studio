---
id: 2025-12-23T02-40-13Z-align-google-model-calls
date: 2025-12-23T02:40:19Z
participants: [human, codex]
models: [gpt-5]
tags: [backend, provider, google]
related_paths:
  - ai-pic-backend/app/services/providers/google_provider/image.py
  - ai-pic-backend/app/services/providers/google_provider/text.py
summary: "Align Google Gemini model calls with repo docs"
---

## User Prompt

- 按 docs/api/googles 内的文档 对齐对google 的模型调用

## Goals

- Align Google Gemini request endpoints to the documented Gemini API paths.
- Match request payload structure to the documented REST examples for image generation.

## Changes

- Updated Gemini text generation to use `v1beta/models/{model}:generateContent` (and `streamGenerateContent`) endpoints.
- Removed redundant `model` field from Gemini image request bodies to match REST examples.

## Validation

- `pytest` (ai-pic-backend) — timed out at 120s with existing failures.
- `./docker/build_prod_images.sh` — success.
- MCP E2E (Chrome): login `geyunfei`/`Gyf@845261`, opened `/environments/aab17f172446462a97e738772337d272`, created a Google Gemini image task, navigated to `/tasks`, and started the new task (status showed “生成中”).

## Next Steps

- Follow up on task completion status and provider errors after the async job finishes.

## Linked Commits

- TBD
