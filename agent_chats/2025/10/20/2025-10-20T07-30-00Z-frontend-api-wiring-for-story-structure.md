---
id: 2025-10-20T07-30-00Z-frontend-api-wiring-for-story-structure
date: 2025-10-20T07:30:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, api]
related_paths:
  - ai-pic-frontend/src/utils/api.ts
summary: "Add experimental API client methods for normalized story structure."
---

## User Prompt

为前端分镜与故事管理后续对接预置 API 客户端方法，先行打通最小读取链路。

## Goals

- 在不改动现有页面的前提下，新增 API 客户端方法：
  - 获取脚本归属的规范化场景、场景节拍与镜头；
  - 获取/创建故事 Treatment（修订）。

## Changes

- 扩展 `src/utils/api.ts` 的 `ApiClient`：增加 `getNormalizedScenes/Beats/Shots`、`getStoryTreatments`、`createStoryTreatment`；
- 导出 `storyStructureAPI` 以便页面/组件按需使用。

## Validation

- 静态检查通过；接口路径与后端新增路由一致。

## Next Steps

- 在 `episodes/[id]/storyboard/page.tsx` 提供开关式试读入口，不破坏现有 JSON 分镜逻辑。

## Linked Commits

- pending（本地增量补丁，后续与此台账一并提交）

