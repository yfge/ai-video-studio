---
id: 2025-10-20T09-35-00Z-backend-tasks-serialize-update
date: 2025-10-20T09:35:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, api]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/tasks.py
summary: "Return serialized TaskResponse on update to ensure parameters are dict, not JSON string."
---

## User Prompt

检查 tasks 并推进后续工作，优先最小化修复与一致性改进。

## Goals

- 统一任务接口的响应：更新任务时返回解析后的 `parameters`（dict），与创建/查询保持一致。

## Changes

- `PUT /api/v1/tasks/{task_id}` 由直接返回 ORM 对象改为通过 `_serialize_task(task)` 返回，避免 `parameters` 为 JSON 字符串导致的类型不一致。

## Validation

- 更改最小、无额外依赖；前端无需改动，即可得到一致的 `parameters` 结构。

## Next Steps

- 可补充 `tasks` 端点的最小路由存在性与序列化测试用例。

## Linked Commits

- pending（本地增量补丁，后续与此台账一并提交）
