---
id: 2025-12-07T14-42-46Z-script-prompt-guard
date: 2025-12-07T14:42:46Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, scripts]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
summary: "Guard script generation when provider response lacks prompt; deepseek model works"
---

## User Prompt

continue

## Goals

- Prevent script generation endpoints from crashing when a provider response omits the `prompt` field.
- Validate with a real model (deepseek:deepseek-chat) to ensure we can produce a structured script instead of falling back.

## Changes

- In sync/async/regenerate script paths, use `result.get(...)` for `generation_prompt` and `ai_model` to avoid KeyError when providers omit these fields.

## Validation

- Manual API call: POST `/api/v1/scripts/generate` with `model=deepseek:deepseek-chat` produced script id 13 (`ai_model=langgraph_script`, word_count=197) with populated scenes, dialogues, and stage directions.

## Next Steps

- Expose model selection in the UI flow and retry with other providers (openai gpt-4o still failing across providers).

## Linked Commits

- pending
