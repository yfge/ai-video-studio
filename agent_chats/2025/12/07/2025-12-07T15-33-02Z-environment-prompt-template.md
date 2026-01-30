---
id: 2025-12-07T15-33-02Z-environment-prompt-template
date: 2025-12-07T15:33:02Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, environment, prompt]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
summary: "Switch environment image generation to a structured prompt template"
---

## User Prompt

使用提示词模板！

## Goals

- Avoid bare minimal prompts when生成环境图/变体 by emitting a structured prompt template that includes名称/类别/标签/描述/附加提示。

## Changes

- Backend `story_structure.py`: added `_compose_environment_prompt` to build a templated prompt (name, category, tags, description, optional extra) and reused it for both text-to-image and image-to-image environment endpoints.

## Validation

- `pytest tests/test_story_structure_endpoints.py -q` (pass; warnings unchanged).

## Next Steps

- Feed the same structured prompt into storyboard generation when environments are used as锚点，并允许前端自定义模板片段/附加提示。

## Linked Commits

- pending
