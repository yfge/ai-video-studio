---
id: 2025-10-20T08-50-00Z-backend-create-endpoints-scenes-shots
date: 2025-10-20T08:50:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, api]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
  - ai-pic-backend/tests/test_story_structure_endpoints.py
  - docs/story-structure-api.md
summary: "Add POST endpoints to create scenes and shots; update docs and route tests."
---

## User Prompt

为规范化叙事结构补充最小创建能力（场景/镜头），并更新文档与路由存在性测试。

## Goals

- 提供：
  - POST `/story-structure/scripts/{script_id}/scenes`
  - POST `/story-structure/scenes/{scene_id}/shots`
- 校验路径参数与请求体 id 一致；返回模型化响应。

## Changes

- 更新 `endpoints/story_structure.py` 增加两条 POST 路由；
- 更新 `tests/test_story_structure_endpoints.py` 断言创建路由已注册；
- 更新文档 `docs/story-structure-api.md` 增补创建端点。

## Validation

- 路由存在性测试通过（不依赖 DB）。

## Next Steps

- 后续添加 PATCH/PUT 端点，支持更新镜头与场景属性，以及批量操作。

## Linked Commits

- pending（本地增量补丁，后续与此台账一并提交）

