---
id: 2025-12-09T06-41-37Z-image-provider-hint
date: 2025-12-09T06:41:37Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, ai-models, bugfix]
related_paths:
  - ai-pic-backend/app/services/ai_service.py
summary: "Honor provider prefix in image generation to avoid cross-provider failures"
---

## User Prompt

日志显示图生图选择 keling 模型仍尝试 openai/volcengine，导致失败。

## Goals

- Ensure model ids with provider prefix (e.g., `keling:kling-image`) route to the correct provider and model name.

## Changes

- In `generate_virtual_ip_image`, split `provider:model` ids into `provider_hint` and `pure_model`; normalized routing now uses `pure_model` for provider-specific branches, sets `prefer_provider` accordingly, and keeps size handling for Volcengine.
- Retained DALL-E and Keling direct paths, now correctly recognizing prefixed ids.

## Validation

- `pytest tests/test_ai_service.py -q`

## Next Steps

- Consider similar provider-prefix handling for other generation endpoints if prefixed ids are allowed.

## Linked Commits

- (this commit)
