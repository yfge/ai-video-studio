---
id: 2026-06-10T12-25-00Z-timeline-pipeline-tracking
date: "2026-06-10T12:25:00Z"
participants:
  - user
  - claude
models:
  - Claude Fable 5
tags:
  - frontend
  - timeline
  - task-polling
related_paths:
  - ai-pic-frontend/src/components/features/episode/useTimelinePipelineTracking.ts
  - ai-pic-frontend/src/components/features/episode/WorkspaceTimelineTabContent.tsx
  - ai-pic-frontend/src/components/features/episode/EpisodeTimelineMainPanel.tsx
summary: 一键流水线任务接入共享 tracker（30 分钟轮询上限），完成后自动按 episode+script 重新拉取 timeline 并走 onTimelineUpdated 刷新链；主面板的静态 task_id 提示升级为实时状态行。
---

# Timeline Pipeline Task Tracking

## User Prompt

生产链路优化 Phase A：一键流水线此前把 pipelineTaskId 存了但从未轮询，主面板只显示静态"任务已创建 task_id=N"，完成后时间轴不刷新。

## Goals

- 流水线任务提交后进入共享 tracker 轮询（流水线含配音/时间轴/分镜多阶段，maxPollMs 提至 30 分钟）。
- 完成后 `listEpisodeTimelines` 按 script_id 匹配最新 timeline → `onTimelineUpdated`（page 级 setSelectedTimelineSpec）自动刷新。
- 主面板静态提示块替换为 `GenerationTaskStatusLine` 实时状态。

## Changes

- 新增 `useTimelinePipelineTracking`（kind="pipeline"，label「时间轴流水线」，trackPipelineTask 经 useCallback 稳定引用）。
- `WorkspaceTimelineTabContent`：移除 `pipelineTaskId` state，提交成功改为 `trackPipelineTask`；prop 链 `pipelineTask` 替换 `pipelineTaskId`。
- `EpisodeTimelineWorkspace` / `EpisodeTimelineMainPanel`：透传 `pipelineTask`，提示块渲染状态行。

## Validation

- `npm run test`：68 个测试全部通过。
- `npm run lint`：0 errors。
- `npm run build`：通过。
- 浏览器证据：与 A7/A8 同批录制。

## Next Steps

- A7：环境图生成自动刷新。

## Linked Commits

- This commit.
