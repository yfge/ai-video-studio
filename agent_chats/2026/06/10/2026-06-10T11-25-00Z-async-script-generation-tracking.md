---
id: 2026-06-10T11-25-00Z-async-script-generation-tracking
date: "2026-06-10T11:25:00Z"
participants:
  - user
  - claude
models:
  - Claude Fable 5
tags:
  - frontend
  - script-generation
  - task-polling
related_paths:
  - ai-pic-frontend/src/hooks/episode/useEpisodeWorkspaceScriptTaskTracking.ts
  - ai-pic-frontend/src/hooks/episode/useEpisodeWorkspaceGenerateScript.ts
  - ai-pic-frontend/src/hooks/episode/useEpisodeWorkspaceController.ts
  - ai-pic-frontend/src/components/features/episode/WorkspaceScriptTabContent.tsx
  - ai-pic-frontend/src/components/shared/notifications/GenerationTaskStatusLine.tsx
  - ai-pic-frontend/tests/episodeScriptTaskTracking.test.ts
summary: async 剧本生成接入共享 tracker：提交后 toast + 剧本 tab 内联状态，完成后自动刷新剧本列表并按 task result_file_path（script:{id}）自动选中新剧本。
---

# Async Script Generation Inline Tracking

## User Prompt

生产链路优化 Phase A：async 剧本生成（默认路径）此前提交后只弹"任务已创建"modal，完成后剧本列表不刷新，操作者以为生成失败。

## Goals

- async 提交后 toast 通知 + 剧本 tab 内联进度状态行。
- 任务完成后自动重新拉取剧本列表、按 `result_file_path = "script:{id}"` 自动选中新剧本（兜底：选不在已知 id 集合中的最新剧本）。
- 新增共享 `GenerationTaskStatusLine` 展示组件（结构化 props，不依赖 feature 层类型）。

## Changes

- 新增 `useEpisodeWorkspaceScriptTaskTracking`：包装共享 tracker（kind="script"），完成回调内拉取 `getEpisodeScripts` → `sortScriptsNewestFirst` → `setScripts` → 选中。
- 修正既有 bug：`resolveScriptIdFromTask` 原正则 `/^script:(\\d+)$/` 中 `\\d` 在正则字面量里匹配字面反斜杠+d，永远匹配不上；新 helper 用 `/^script:(\d+)$/` 并导出（A4 复用）。
- `useEpisodeWorkspaceGenerateScript` 增加 `onTaskQueued`/`notify` 可选参数；async 成功分支改 toast 文案并进入轮询。
- `useEpisodeWorkspaceController` 实例化 tracking（useToast 注入 notify），返回 `scriptTask`；`useEpisodeWorkspaceScriptActions` 透传 `onScriptTaskQueued`/`notify`。
- `WorkspaceScriptTabContent`/`WorkspaceActiveTabContent`/workspace page 透传 `scriptTask` 并渲染内联状态行（无剧本和有剧本两种布局都显示）。
- 新增 `src/components/shared/notifications/GenerationTaskStatusLine.tsx` 并从 barrel 导出。
- 新测试 `tests/episodeScriptTaskTracking.test.ts`：result path 解析（含修正后的正则）+ 完成后刷新列表并选中任务产出剧本。

## Validation

- `npm run test`：68 个测试全部通过。
- `npm run lint`：0 errors。
- `npm run build`：通过。
- 浏览器证据：按计划与 A4/A5 同批在 dev 栈录制（见后续 ledger）。

## Next Steps

- A4：重新生成剧本的自带轮询统一到共享 tracker。

## Linked Commits

- This commit.
