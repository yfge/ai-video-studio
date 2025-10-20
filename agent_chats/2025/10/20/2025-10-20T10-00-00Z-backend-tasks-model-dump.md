---
id: 2025-10-20T10-00-00Z-backend-tasks-model-dump
date: 2025-10-20T10:00:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, api, cleanup]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/tasks.py
summary: "Replace deprecated Pydantic .dict() with .model_dump() in tasks update endpoint."
---

## User Prompt

将 tasks 更新端点中的 Pydantic v2 过时 `.dict()` 替换为 `.model_dump()`，保持最小变更提交。

## Goals

- 消除 Pydantic v2 弃用警告，代码面向 v2 API。

## Changes

- `PUT /api/v1/tasks/{task_id}`：`task_data.dict(exclude_unset=True)` → `task_data.model_dump(exclude_unset=True)`。

## Validation

- 运行 `pytest tests/test_tasks_minimal.py -q` 通过；Pydantic 弃用警告减少。

## Next Steps

- 后续逐步替换其余 `.dict()` 用法（单独原子提交）。

## Linked Commits

- pending（本地此次改动将与本账本条目一并提交）

