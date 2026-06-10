---
id: 2026-06-10T13-00-00Z-video-completion-render-refresh
date: "2026-06-10T13:00:00Z"
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
  - ai-pic-frontend/src/components/features/episode/useTimelineRenderJobs.ts
  - ai-pic-frontend/src/components/features/episode/useTimelineGenerationRefresh.ts
  - ai-pic-frontend/src/components/features/episode/EpisodeTimelineWorkspace.tsx
summary: 片段生成任务完成后的刷新链加入渲染 job 列表刷新——后端在片段视频成功后自动排最终渲染，现在渲染面板会立即显示新 job 并由既有 4s 轮询接管。
---

# Render Panel Refresh After Clip Video Completion

## User Prompt

生产链路优化 Phase A 收尾：片段视频 rework 成功后后端会自动排最终渲染 job（`apply_timeline_rework_result` → `queue_provider_rework_render_job`，已在探查中确认），但渲染面板不刷新，操作者看不到自动排上的渲染。

## Goals

- 片段生成任务（含视频）完成后的统一刷新链中加入渲染 job 列表刷新。
- 新 job 出现后由 `useTimelineRenderJobs` 既有的 queued/running 4s 轮询自动接管直至完成。

## Changes

- `useTimelineRenderJobs`：return 暴露 `reloadRenderJobs`。
- `useTimelineGenerationRefresh`：新增可选 `reloadRenderJobs`，在刷新 clip assets 后调用。
- `EpisodeTimelineWorkspace`：把 `reloadRenderJobs` 接入 `handleGenerationCompleted`。

## Validation

- `npm run test`：68 个测试全部通过。
- `npm run lint`：0 errors。
- 浏览器证据：与 A6/A7 同批录制（Phase A 浏览器验证会话）。

## Next Steps

- Phase B：B1 workbench 状态修正（后端）。
- Phase A 浏览器证据批次录制。

## Linked Commits

- This commit.
