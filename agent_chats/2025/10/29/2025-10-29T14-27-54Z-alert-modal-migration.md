---
id: 2025-10-29T14-27-54Z-alert-modal-migration
date: 2025-10-29T14:27:54Z
participants: [human, codex]
models: [gpt-5-codex]
tags: [frontend, ui]
related_paths:
  - ai-pic-frontend/src/components/AlertModalProvider.tsx
  - ai-pic-frontend/src/app/layout.tsx
  - ai-pic-frontend/src/app/stories/page.tsx
  - ai-pic-frontend/src/app/stories/[id]/page.tsx
  - ai-pic-frontend/src/app/virtual-ip/page.tsx
  - ai-pic-frontend/src/app/virtual-ip/[id]/page.tsx
  - ai-pic-frontend/src/app/virtual-ip/[id]/images/page.tsx
  - ai-pic-frontend/src/app/episodes/[id]/page.tsx
  - ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx
  - ai-pic-frontend/src/app/scripts/[id]/page.tsx
  - ai-pic-frontend/src/app/tasks/page.tsx
summary: "Replaced blocking window.alert calls with a shared modal provider and rewired all affected pages to use contextual feedback."
---

## User Prompt

把所有的 `alert` 都改成 modal 组件。

## Goals

- Provide a central modal experience instead of browser alerts.
- Update every page that surfaced alerts to use the new API.

## Changes

- Added `AlertModalProvider` with context-powered modal UI and wired it through `layout.tsx`.
- Refactored story, episode, script, task, and virtual IP pages (including images and storyboard views) to import `useAlertModal` and replace every `alert(...)` call with `showAlert`.
- Normalized success/error messaging variants so each flow reports via modal instead of the blocking browser dialog.

## Validation

- 手动：通过浏览器执行故事→剧集→剧本→分镜的完整流程，确认原本的 alert 现在弹出 modal（任务创建、剧本生成、分镜保存）并未阻塞流程；任务列表展示成功和失败记录。
- `npm run lint -- --file` 在若干改动文件上仍会触发既有 `any` 相关报错，未在本次范围内修复。

## Next Steps

- 视需要整合 Toast/Modal 通知策略，统一成功与提示类消息的展示逻辑。

## Linked Commits

- _pending_
