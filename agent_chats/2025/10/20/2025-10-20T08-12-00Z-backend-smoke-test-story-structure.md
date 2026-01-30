---
id: 2025-10-20T08-12-00Z-backend-smoke-test-story-structure
date: 2025-10-20T08:12:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, testing]
related_paths:
  - ai-pic-backend/tests/test_story_structure_endpoints.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
  - ai-pic-backend/app/api/v1/api.py
summary: "Add route presence smoke test for new story-structure endpoints (no DB required)."
---

## User Prompt

为新增的规范化叙事结构端点增加最小的路由存在性测试，避免回归。

## Goals

- 在不依赖数据库的前提下，验证 `/api/v1/story-structure/*` 相关路径已挂载。

## Changes

- 新增 `tests/test_story_structure_endpoints.py`：通过 `create_app()` 构建应用，枚举 `APIRoute.path` 集合并断言目标路径存在。

## Validation

- 测试仅做路由存在性检查，避免引入 DB 前置条件；与现有失败用例互不影响。

## Next Steps

- 后续可补充端到端测试，在可控的测试 DB 中写入少量样本后调用端点校验响应结构。

## Linked Commits

- pending（本地增量补丁，后续与此台账一并提交）
