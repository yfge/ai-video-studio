---
id: 2025-10-20T07-20-00Z-story-structure-api-minimal
date: 2025-10-20T07:20:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [backend, api]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/story_structure.py
  - ai-pic-backend/app/api/v1/api.py
summary: "Introduce minimal story-structure endpoints and register router."
---

## User Prompt

实现最小读写 API，提供对脚本关联场景、场景节拍/镜头与故事修订（treatment）的读取和创建能力。

## Goals

- 不影响现有接口的前提下，提供：
  - GET `/story-structure/scripts/{script_id}/scenes`
  - GET `/story-structure/scenes/{scene_id}/beats`
  - GET `/story-structure/scenes/{scene_id}/shots`
  - GET `/story-structure/stories/{story_id}/treatments`（支持 `latest_only`）
  - POST `/story-structure/stories/{story_id}/treatments`

## Changes

- 新增 `endpoints/story_structure.py` 并在 `api.py` 中注册到 `API_V1` 路由树。

## Validation

- 静态检查通过；端点参数与响应模型对齐 `schemas.story_structure`。
- 后续将通过集成测试与前端试读进一步验证。

## Next Steps

- 在前端分镜页添加“实验性读取规范化场景/镜头”的调用入口（特性开关）。
- 后端逐步补充创建/更新场景与镜头的接口与校验。

## Linked Commits

- pending（本地增量补丁，后续与此台账一并提交）

