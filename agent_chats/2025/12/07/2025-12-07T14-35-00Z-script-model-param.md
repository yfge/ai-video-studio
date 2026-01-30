---
id: 2025-12-07T14-35-00Z-script-model-param
date: 2025-12-07T14:35:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, scripts, generation]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/scripts.py
summary: "Allow script regeneration to pass the configured model/provider/temperature"
---

## User Prompt

好的，传入实际模型

## Goals

- Make script regeneration honor the originally selected model/provider instead of always using fallback.

## Changes

- In `/api/v1/scripts/{id}/regenerate`, parse `generation_params.model` (provider:model) and temperature, and forward them to `ai_service.generate_script`, enabling real providers to be used during regeneration.

## Validation

- Not run (small backend wiring change).

## Next Steps

- Regenerate a script via the UI with a real model configured to confirm the provider call path is hit; monitor backend logs.

## Linked Commits

- pending
