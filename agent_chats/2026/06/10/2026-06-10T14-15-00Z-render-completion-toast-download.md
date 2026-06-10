---
id: 2026-06-10T14-15-00Z-render-completion-toast-download
date: "2026-06-10T14:15:00Z"
participants:
  - user
  - claude
models:
  - Claude Fable 5
tags:
  - frontend
  - render
  - ux
related_paths:
  - ai-pic-frontend/src/components/features/episode/useTimelineRenderJobs.ts
  - ai-pic-frontend/src/components/features/episode/EpisodeTimelineRenderPanel.tsx
  - ai-pic-frontend/tests/timelineWorkspaceLayout.test.tsx
summary: 渲染 job 从 queued/running 转 succeeded/failed 时弹 toast；成功后输出区升级为绿色高亮块 + 主按钮「下载成片」+ 新标签页打开链接，替代易被忽略的小字链接。
---

# Render Completion Toast And Prominent Download

## User Prompt

生产链路优化 Phase B3：成片输出此前只有渲染面板底部一行小字链接「打开输出文件」，渲染完成无任何主动通知，操作者容易错过导出结果。

## Goals

- 轮询中渲染 job 状态从 queued/running 转为 succeeded → 成功 toast；转为 failed → 错误 toast。
- 成功输出区升级：绿色高亮块 + 「{类型}已就绪」+ 主按钮「下载成片」（download 属性）+ 次级「在新标签页打开」。

## Changes

- `useTimelineRenderJobs`：`prevJobStatusRef` 记录上一轮 (id, status)，仅在同一 job 且前态为活跃态时对终态转换发 toast（首次加载历史已完成 job 不会误报）。
- `EpisodeTimelineRenderPanel`：输出链接区域重构为高亮下载块。
- `timelineWorkspaceLayout.test.tsx`：workspace wrapper 增包 `ToastProvider`（hook 现在依赖 useToast）。

## Validation

- `npm run test`：70 个测试全部通过。
- `npm run lint`：0 errors。
- 浏览器证据：Phase B 批次录制（渲染需可渲染时间轴，与 B4b 同场景验证）。

## Next Steps

- B4a：后端 timeline clip-tasks 列表端点。

## Linked Commits

- This commit.
