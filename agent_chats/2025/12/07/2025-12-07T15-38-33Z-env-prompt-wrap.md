---
id: 2025-12-07T15-38-33Z-env-prompt-wrap
date: 2025-12-07T15:38:33Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, environment, prompt]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
summary: "Wrap environment image prompts in a structured template even when frontend sends a prompt"
---

## User Prompt

测试，用chrome自测 / 使用提示词模板！

## Goals

- Ensure environment 文生图/图生图 always use the structured prompt template, even if the frontend sends a prompt string.
- Validate via Chrome that the endpoint still works after the change.

## Changes

- Backend `story_structure.py`: both generate and variant endpoints now pass any provided prompt into `_compose_environment_prompt`, so prompts are always wrapped with name/category/tags/description context.

## Validation

- `pytest tests/test_story_structure_endpoints.py -q` (pass).
- Chrome manual: `/environments` → Seedream 4.5 → “一键生成参考图” succeeded (HTTP 200, new image saved). Note: log still shows raw request body from frontend, backend wraps it internally before dispatch.

## Next Steps

- Surface a UI hint that prompts are auto-wrapped with环境信息; consider exposing a preview of the final composed prompt for transparency.

## Linked Commits

- pending
