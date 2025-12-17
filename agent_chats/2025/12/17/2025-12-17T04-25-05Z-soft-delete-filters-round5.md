---
id: 2025-12-17T04-25-05Z-soft-delete-filters-round5
date: 2025-12-17T04:25:05Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, api]
related_paths:
  - ai-pic-backend/app/services/story_structure_service.py
summary: "Completed soft-delete filtering in story structure service"
---

## User Prompt

- 检查并补全剩余端点的软删过滤。

## Goals

- story_structure service 统一过滤软删，包含 step outlines、script/scene creation env check、beats listing。

## Changes

- `story_structure_service`: step outlines list、script/env lookups、scene beat listing均使用 `_not_deleted`，保证关联检查与读取不返回软删记录。

## Validation

- 未运行自动化测试。

## Next Steps

- 复查 prompts/diagnostic 是否需要数据过滤；运行 pytest。

## Linked Commits

- (pending)
