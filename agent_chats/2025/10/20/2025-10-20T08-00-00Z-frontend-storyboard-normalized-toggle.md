---
id: 2025-10-20T08-00-00Z-frontend-storyboard-normalized-toggle
date: 2025-10-20T08:00:00Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, feature-flag]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
summary: "Add experimental toggle to read normalized scenes/shots in storyboard without breaking existing flows."
---

## User Prompt

按计划为分镜页面提供特性开关，以在不改变现有逻辑的前提下尝试读取规范化场景/镜头数据。

## Goals

- 默认保持现状；勾选“使用规范化结构（实验）”后：
  - 读取并显示 `story-structure` API 的场景列表；
  - 点击场景时根据 `scene_number` 选中分镜帧；
  - 显示该场景的规范化镜头摘要（shot_number/shot_type）。

## Changes

- 更新 `episodes/[id]/storyboard/page.tsx`：
  - 新增状态：`useNormalized`、`normalizedScenes`、`normalizedShots`、`selectedNormalizedSceneId`、`normalizedLoading`；
  - 新增 `uiScenes` 派生列表以统一渲染；
  - 顶部加入实验性复选框切换；
  - 左侧场景列表在开关开启时渲染规范化场景，并在切换/首次加载时重置当前选中场景；
  - 右侧在分镜帧区域上方附加“规范化镜头（实验）”条，展示 shots 摘要。

## Validation

- 默认关闭时行为不变；开启后若后端无数据则友好提示“暂无规范化场景/镜头”。
- 仅改动前端渲染与增量请求，不影响现有 API 调用与保存逻辑。

## Next Steps

- 后续可在该页面中加入按 normalized 数据生成/映射分镜帧的操作入口。

## Linked Commits

- pending（本地增量补丁，后续与此台账一并提交）

