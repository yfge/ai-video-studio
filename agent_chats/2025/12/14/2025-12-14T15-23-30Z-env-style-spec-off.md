---
id: 2025-12-14T15-23-30Z-env-style-spec-off
date: 2025-12-14T15:23:30Z
participants: [human, codex]
models: [gpt-4o]
tags: [backend, environment, style]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
summary: "Disable style_spec for environment image generation to avoid character prompts"
---
## User Prompt
- 环境文生图提示词包含 STYLE_SPEC（动漫人物相关字段），导致环境里“总有人”。

## Goals
- 环境图生成不再透传 style_spec（角色/镜头相关风格），减少人物入画的概率。

## Changes
- 添加 `_sanitize_environment_style_spec`，环境文生图/图生图、异步任务和变体生成都强制将 style_spec 置空，不再传给模型。

## Validation
- `pytest tests/test_tasks_minimal.py -q`。

## Next Steps
- 线上重试环境生图，确认提示词不再出现 STYLE_SPEC 段落且人物出现概率降低；如需保留部分环境风格字段，可后续添加仅环境相关的白名单字段。

## Linked Commits
- fix(backend): remove style spec from environment images
