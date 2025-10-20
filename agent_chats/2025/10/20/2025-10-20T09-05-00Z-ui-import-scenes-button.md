---
id: 2025-10-20T09-05-00Z-ui-import-scenes-button
date: 2025-10-20T09:05:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, backend, api]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
  - ai-pic-frontend/src/utils/api.ts
  - ai-pic-backend/app/services/story_structure_service.py
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
  - docs/story-structure-api.md
summary: "Add experimental UI button to import normalized scenes from existing JSON via new seed API endpoint."
---

## User Prompt

在分镜页加入“从现有分镜导入场景（实验）”按钮，通过后端新端点触发 JSON 场景 → 规范化 scenes 的导入。

## Goals

- 提供一键导入体验；导入完成后在开关开启时刷新场景列表。

## Changes

- 后端：
  - `story_structure_service.seed_scenes_from_script_json` 服务函数；
  - POST `/api/v1/story-structure/scripts/{script_id}/seed-from-json?dry_run=false` 端点；
  - 文档 `docs/story-structure-api.md` 增补端点说明；
  - 路由存在性测试更新。
- 前端：
  - `storyStructureAPI.seedScenesFromJson(scriptId)` 方法；
  - 在分镜页顶部加入按钮，执行导入并在使用规范化结构时自动刷新场景列表。

## Validation

- 不依赖外部服务；导入结果以弹窗提示数量，失败时提示错误。

## Next Steps

- 补充批量导入镜头（shots）与更新端点；支持幂等重跑校验统计。

## Linked Commits

- pending（本地增量补丁，后续与此台账一并提交）

