---
id: 2025-12-07T12-10-00Z-api-client-export
date: 2025-12-07T12:10:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend]
related_paths:
  - ai-pic-frontend/src/utils/api.ts
summary: "Export apiClient as a named export to fix undefined storyStructureAPI"
---

## User Prompt

- 操作失败：Cannot read properties of undefined (reading 'getNormalizedScenes')

## Goals

- 确保 apiClient 既有默认导出也有具名导出，避免引用到 undefined。

## Changes

- 将全局 ApiClient 实例改为具名导出 `apiClient`，同时保留默认导出，修复 SceneStructurePanel 等组件对具名导入的依赖。

## Validation

- npm --prefix ai-pic-frontend run lint

## Next Steps

- 浏览器重新加载分镜/场景相关页面，确认错误不再出现。

## Linked Commits

- (pending)
