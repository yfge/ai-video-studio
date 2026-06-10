---
id: 2026-06-10T12-45-00Z-environment-image-auto-refresh
date: "2026-06-10T12:45:00Z"
participants:
  - user
  - claude
models:
  - Claude Fable 5
tags:
  - frontend
  - environments
  - task-polling
related_paths:
  - ai-pic-frontend/src/components/features/environments/EnvironmentSidePanel.tsx
  - ai-pic-frontend/src/components/features/environments/EnvironmentDetailState.ts
  - ai-pic-frontend/src/components/features/environments/EnvironmentDetailView.tsx
summary: 环境参考图生成接入共享 tracker：提交 toast + 内联状态行，任务完成后自动刷新环境图列表，对齐 IP 图片的自动刷新体验。
---

# Environment Image Generation Auto-Refresh

## User Prompt

生产链路优化 Phase A：环境图生成此前提交后弹"任务将在后台执行，完成后刷新本页查看新图片"的阻塞 modal，操作者必须手动刷新页面，与 IP 图片的自动刷新体验不一致。

## Goals

- 生成任务提交 → toast（带 task_id）+ 按钮下内联状态行。
- 任务完成 → 自动重新加载环境详情与图片列表。

## Changes

- `EnvironmentDetailState`：return 暴露 `reload`（复用既有 load）。
- `EnvironmentSidePanel`：新增 `onImagesGenerated` prop；内部 `useToast` + `useGenerationTaskTracker<"environment-images">`（label「环境参考图」）；提交成功 toast + track；按钮下渲染 `GenerationTaskStatusLine`。
- `EnvironmentDetailView`：`onImagesGenerated={state.reload}`。

## Validation

- `npm run test`：68 个测试全部通过。
- `npm run lint`：0 errors。
- 浏览器证据：与 A6/A8 同批录制。

## Next Steps

- A8：片段视频完成后渲染面板自动刷新。

## Linked Commits

- This commit.
