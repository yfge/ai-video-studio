---
id: 2025-12-15T12-33-49Z-frontend-episode-audio-controls
date: 2025-12-15T12:33:49Z
participants: [human, codex]
models: [gpt-5.2]
tags: [frontend, episode, audio, timeline]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/page.tsx
  - ai-pic-frontend/src/utils/api.ts
  - tasks.md
summary: "Added Episode page controls to trigger dialogue audio, timeline, and storyboard placeholder tasks"
---

## User Prompt

在 Episode 内提供“生成对白音轨 / 生成时间轴 / 生成分镜帧”入口，展示进度、失败原因、版本与重试/复用，并保持原子提交与 tasks.md 更新。

## Goals

- 在 Episode 详情页为选定剧本提供 3 个入口按钮：对白音轨、时间轴、分镜占位
- 支持 overwrite/复用参数，并在页面内轮询任务状态展示 progress/failure
- 同步更新 `utils/api.ts` 补齐调用方法与类型字段

## Changes

- `ai-pic-frontend/src/utils/api.ts`：新增 3 个脚本级异步 API 调用（scene 音轨、episode 时间轴、storyboard from audio timeline），并补齐 `StoryboardFrame.start_ms/end_ms` 与 `NormalizedScene.metadata`
- `ai-pic-frontend/src/app/episodes/[id]/page.tsx`：新增“对白音轨与时间轴”面板（选择剧本、生成按钮、overwrite 参数、任务轮询与状态展示）
- `tasks.md`：勾选前端入口工作项

## Validation

- `cd ai-pic-frontend && npm run lint`

## Next Steps

- Chrome 端到端验证：Episode → 生成对白音轨 → 生成时间轴 → 生成分镜帧占位（并记录 OSS URL/frames 数量等结果）

## Linked Commits

- (pending)
