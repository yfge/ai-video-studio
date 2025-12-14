---
id: 2025-12-14T15-30-51Z-env-style-preset-off
date: 2025-12-14T15:30:51Z
participants: [human, codex]
models: [gpt-4o]
tags: [backend, environment, style]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
summary: "Strip style preset/spec from environment images to avoid character-style prompts"
---
## User Prompt
- 环境文生图日志仍显示 STYLE_SPEC（动漫风格），导致环境里出现人物。

## Goals
- 环境图生成彻底不透传 style_preset/style_spec（即使请求携带），只保留基础 style 字段。

## Changes
- 增加 `_sanitize_environment_style`：保留 style（默认 realistic），强制将 style_preset_id 和 style_spec 置空。
- 应用于环境文生图同步/异步、worker 执行、图生图变体三个路径，防止 style prompt 拼接。

## Validation
- `pytest tests/test_tasks_minimal.py -q`。

## Next Steps
- 线上再跑环境生图，确认提示词不再带 STYLE_SPEC；若仍有角色入画，可进一步收紧（例如强制 style=realistic 或加入“无人物”描述）。

## Linked Commits
- fix(backend): strip style preset in environment images
