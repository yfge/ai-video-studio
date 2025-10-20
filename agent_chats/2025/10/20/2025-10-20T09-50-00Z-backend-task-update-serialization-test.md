---
id: 2025-10-20T09-50-00Z-backend-task-update-serialization-test
date: 2025-10-20T09:50:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, testing]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/tasks.py
  - ai-pic-backend/tests/test_tasks_minimal.py
summary: "Add unit test to ensure PUT /tasks returns TaskResponse with parameters as dict."
---

## User Prompt

检查 tasks 并开展进一步工作，新增最小测试保障之前的一致性修复。

## Goals

- 验证更新任务接口返回的 `parameters` 为字典，保持与创建/查询一致。

## Changes

- 新增 `tests/test_tasks_minimal.py`：创建任务后更新参数并断言响应结构。

## Validation

- 运行 `pytest tests/test_tasks_minimal.py -q` 通过（1 passed），仅有已知 Pydantic/SQLAlchemy 警告。

## Next Steps

- 后续可将 `dict()` 迁移为 `model_dump()`，逐步清理 Pydantic v2 警告（另行提交）。

## Linked Commits

- pending（本地增量补丁将与此台账条目一并提交）

