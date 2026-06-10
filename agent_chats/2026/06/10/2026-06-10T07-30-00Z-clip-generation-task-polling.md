---
id: 2026-06-10T07-30-00Z-clip-generation-task-polling
date: "2026-06-10T07:30:00Z"
participants:
  - user
  - claude
models:
  - Claude Fable 5
tags:
  - frontend
  - timeline
  - clip-storyboard
  - ux
related_paths:
  - ai-pic-frontend/src/components/features/episode/useTimelineClipGenerationTaskTracker.ts
  - ai-pic-frontend/src/components/features/episode/TimelineClipTaskStatusLine.tsx
  - ai-pic-frontend/src/components/features/episode/useTimelineClipProviderGenerationActions.ts
  - ai-pic-frontend/src/components/features/episode/TimelineClipProviderReworkControls.tsx
  - ai-pic-frontend/src/components/features/episode/EpisodeTimelineWorkspace.tsx
  - ai-pic-frontend/tests/timelineClipGenerationTaskTracker.test.ts
summary: 为片段故事板/首尾帧/视频生成任务增加内联轮询进度、完成后自动刷新 timeline spec 与资产，并放大故事板预览支持查看原图。
---

# Clip Generation Task Polling And Inline Refresh

## User Prompt

完成整体的分镜生成链路（IP 图/环境图绑定、故事板生成、视频生成），同时调整优化 UI 做到用户友好；分步提交，保持工作区干净。本提交解决最大的体验断点：提交生成任务后没有任何进度反馈，必须离开页面去任务列表查看，故事板生成完成后预览也不会自动刷新。

## Goals

- 故事板/首尾帧/片段视频任务提交后，在卡片内联显示生成进度。
- 任务完成后自动刷新 timeline spec 和 clip assets，故事板预览、panel 引用即时可见。
- 任务失败时把后端 error_message 直接显示在卡片里。
- 故事板参考图预览放大并支持点击查看原图。

## Changes

- 新增 `useTimelineClipGenerationTaskTracker`：按任务类型轮询 `taskAPI.getTask`（默认 4s 间隔、15 分钟超时），终态触发通知与刷新回调，卸载时清理定时器。
- 新增 `TimelineClipTaskStatusLine`：内联展示 pending/processing/completed/failed/timeout 状态，跨 clip 的任务状态不串显。
- `useTimelineClipProviderGenerationActions` 新增 `onTaskQueued` 回调；storyboard/keyframes 提交后进入轮询。
- `TimelineClipProviderReworkControls` 接入 tracker，video rework 提交后同样轮询；新增 `onGenerationCompleted` prop。
- `TimelineClipProviderReworkCards` / `StoryboardReferenceCard` / `TimelineClipKeyframeCard` / `TimelineClipVideoReworkCard` 透传任务状态并渲染状态行。
- 故事板预览图从 192px 提升到 288px，并包一层 `<a target="_blank">` 支持查看大图。
- 刷新链路：`page.tsx` 已有的 `onTimelineUpdated={setSelectedTimelineSpec}` 透传到 `WorkspaceTimelineTabContent` → `EpisodeTimelineWorkspace`；workspace 内 `handleGenerationCompleted` 在任务完成后重新拉取 `timelineAPI.getTimeline` 并刷新 clip assets。

## Validation

- `npm run test`：56 个测试全部通过（含新增 `timelineClipGenerationTaskTracker.test.ts` 3 个用例：轮询到完成并触发刷新、失败信息透出、跨 clip 状态隐藏）。
- `npm run lint`：0 errors（仅两条无关文件的既有 `no-img-element` warnings）。
- `npm run build`：通过。

## Next Steps

- 参考图选择体验：默认预选 + 全选/清空 + 选中计数。
- 视频表单友好化：模型下拉、比例预设、字段说明。

## Linked Commits

- This commit.
