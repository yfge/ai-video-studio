---
id: 2026-01-20T01-02-54Z-frontend-auto-timeline-pipeline
date: 2026-01-20T01:02:54Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, episode, timeline, ux]
related_paths:
  - ai-pic-frontend/src/hooks/episode/useEpisodeWorkspaceController.ts
  - ai-pic-frontend/src/components/features/episode/WorkspaceTimelineTabContent.tsx
summary: "Make '生成时间轴' start the timeline pipeline automatically"
---

## User Prompt

为什么没有生成时间轴；并要求做短剧全流程测试（脚本/时间轴/分镜等都要能跑通）。

## Goals

- 点击「生成时间轴」不再只是跳转页面，而是直接创建时间轴流水线任务
- 避免开发环境 StrictMode 造成重复自动触发、产生多条重复任务

## Changes

- `useEpisodeWorkspaceController.handleGenerateTimeline` 在跳转到时间轴页时附带 `autoTimelinePipeline=<runId>` 参数
- `WorkspaceTimelineTabContent` 检测该参数后自动调用 `generateTimelinePipelineAsync` 并清理参数；用 `sessionStorage` 记录 runId，防止重复触发

## Validation

- `cd ai-pic-frontend && npm run lint`
- `./docker/build_prod_images.sh`
- Chrome (MCP): 打开剧集工作台概览页，点击「生成时间轴」后自动进入时间轴页并弹出提示「一键流水线任务已创建」，任务管理页出现对应「一键时间轴流水线」任务

## Next Steps

- 时间轴流水线完成后，联动分镜页解除「未生成时间轴」的阻塞提示
- 继续排查/优化剧本质量与提示词模板（每集爽点）

## Linked Commits

- fix(frontend): auto-run timeline pipeline from workspace header
