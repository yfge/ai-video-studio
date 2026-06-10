---
id: 2026-06-10T12-05-00Z-story-episode-generation-tracking
date: "2026-06-10T12:05:00Z"
participants:
  - user
  - claude
models:
  - Claude Fable 5
tags:
  - frontend
  - episode-generation
  - task-polling
related_paths:
  - ai-pic-frontend/src/hooks/useStoryEpisodeGeneration.ts
  - ai-pic-frontend/src/components/features/story-detail/EpisodeGeneratePanel.tsx
  - ai-pic-frontend/src/components/features/stories/StoryProductionDetail.tsx
summary: 故事详情页 async 剧集生成接入共享 tracker：提交 toast、面板内联状态行、任务完成后自动刷新故事详情（剧集列表），替代"已创建任务请稍后在任务页查看"。
---

# Story Episode Generation Tracking

## User Prompt

生产链路优化 Phase A：故事详情页 async 生成剧集此前提交后只弹"已创建任务，请稍后在任务页查看进度"，完成后剧集列表不刷新。

## Goals

- async 提交成功 → toast（带 task_id）并进入共享 tracker 轮询。
- 任务完成 → 自动调用 `loadData`（onRefreshAfterSync）刷新故事详情与剧集列表 + 完成 toast。
- 生成剧集面板顶部内联 `GenerationTaskStatusLine`。

## Changes

- `useStoryEpisodeGeneration`：内部 `useToast` + `useGenerationTaskTracker<"episodes">`（label「剧集」），async 成功分支 toast + track，返回 `episodesTask`（经 `useStoryDetail` 的 spread 自动透出）。
- `EpisodeGeneratePanel`：新增 `episodesTask` prop，标题上方渲染状态行。
- `StoryProductionDetail`：解构并透传 `episodesTask`；合并一处多行 import（prettier-ignore）以保持 250 行限制内（249 行）。

## Validation

- `npm run test`：68 个测试全部通过。
- `npm run lint`：0 errors。
- `python scripts/check_repo_contracts.py --mode diff`：StoryProductionDetail 249 行达标。
- 浏览器证据：与 A3/A4 同批录制。

## Next Steps

- A6：一键流水线 pipelineTaskId 接入轮询。

## Linked Commits

- This commit.
