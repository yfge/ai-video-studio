---
id: 2026-06-10T15-05-00Z-render-readiness-inflight-clips
date: "2026-06-10T15:05:00Z"
participants:
  - user
  - claude
models:
  - Claude Fable 5
tags:
  - frontend
  - timeline
  - render
related_paths:
  - ai-pic-frontend/src/components/features/episode/useTimelineActiveClipTasks.ts
  - ai-pic-frontend/src/components/features/episode/EpisodeTimelineRenderModel.ts
  - ai-pic-frontend/src/components/features/episode/EpisodeTimelineRenderPanel.tsx
  - ai-pic-frontend/src/utils/api/endpoints/timeline.endpoints.ts
  - ai-pic-frontend/tests/timelineWorkspaceHelpers.test.ts
summary: 渲染就绪检查感知 in-flight 任务：通过 GET /timelines/{id}/clip-tasks 轮询（10s），缺片段原因区分「生成中（蓝）」与「缺失（琥珀）」，避免操作者对生成中的片段重复触发重做。
---

# Render Readiness Shows Generating For In-Flight Clips

## User Prompt

生产链路优化 Phase B4b：渲染就绪检查不感知正在生成的视频任务，操作者看到「缺 N 个片段」会误以为没在生产而重复触发 rework。

## Goals

- `buildTimelineRenderReadiness` 接收 in-flight clip 任务集合，missing 原因区分 `generating` / `missing_video_url`。
- 渲染面板缺失提示拆为「生成中片段（完成后自动可渲染）」蓝色行 + 「缺失片段」琥珀行。
- clip-tasks 每 10s 轮询（B4a 端点），与 readiness 折叠进单一 hook 控制 workspace 行数。

## Changes

- `EpisodeTimelineRenderModel.buildTimelineRenderReadiness` 增加可选 `activeClipTaskIds: ReadonlySet<string>` 参数。
- 新增 `useTimelineRenderReadinessWithTasks`（useTimelineActiveClipTasks.ts）：轮询 clip-tasks → activeClipTaskIds → 内部 memo readiness。
- `EpisodeTimelineWorkspace` 用该 hook 替换原 readiness memo（243 行守住限制）。
- `EpisodeTimelineRenderPanel`：`MissingClipsSummary` 组件分组展示。
- 前端类型 `TimelineClipTaskItem/ListResponse` + `timelineAPI.listTimelineClipTasks`。
- `timelineWorkspaceHelpers.test.ts`：新增 generating/missing 分类用例并固化原 reason 断言。

## Validation

- `npm run test`：71 个测试全部通过。
- `npm run lint`：0 errors；`npm run build` 通过。

## Next Steps

- B5：IP readiness 告警。

## Linked Commits

- This commit.
