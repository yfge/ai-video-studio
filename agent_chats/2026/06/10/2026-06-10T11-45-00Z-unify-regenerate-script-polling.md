---
id: 2026-06-10T11-45-00Z-unify-regenerate-script-polling
date: "2026-06-10T11:45:00Z"
participants:
  - user
  - claude
models:
  - Claude Fable 5
tags:
  - frontend
  - script-generation
  - refactor
related_paths:
  - ai-pic-frontend/src/hooks/episode/useEpisodeWorkspaceRegenerateScript.ts
  - ai-pic-frontend/src/hooks/useGenerationTaskTracker.ts
summary: 重新生成剧本的自带 2s 阻塞轮询循环替换为共享 useGenerationTaskTracker；共享 tracker 新增 onFailed 回调供清理 sessionStorage pending 状态。
---

# Unify Regenerate-Script Polling Onto Shared Tracker

## User Prompt

生产链路优化 Phase A：重新生成剧本此前有自己的 2s×180 次阻塞 await 轮询（与新共享 tracker 并存两套逻辑），统一到共享 tracker。

## Goals

- `useEpisodeWorkspaceRegenerateScript` 的 `pollTaskUntilDone` 阻塞循环移除，改用共享 tracker 后台轮询。
- 保留 sessionStorage pending 恢复（页面刷新后续跟踪）、完成后刷新列表+选中新剧本+版本号成功提示。
- 共享 tracker 增加可选 `onFailed(kind, taskId, error)` 回调（失败时清 pending，避免刷新后重复跟踪已失败任务）。

## Changes

- `useGenerationTaskTracker`：新增 `onFailed` 可选回调（ref 化、failed 分支触发），向后兼容。
- `useEpisodeWorkspaceRegenerateScript` 重写：提交后 `tracker.track("regenerate", taskId)`；`regenerating = submitting || tracker.isActive`；完成回调复用 `resolveScriptIdFromTask`（A3 修正版正则）+ 刷新选中流程；挂载时一次性恢复 pending 跟踪。
- `useEpisodeWorkspaceScriptActions` 向 regenerate hook 透传 `notify`（提交/成功消息走 toast，错误保留 modal）。

## Validation

- `npm run test`：68 个测试全部通过。
- `npm run lint`：0 errors。
- 浏览器证据：与 A3/A5 同批录制。

## Next Steps

- A5：故事详情页剧集生成接入 tracker。

## Linked Commits

- This commit.
