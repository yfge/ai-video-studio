---
id: 2025-12-17T11-26-57Z-remove-script-storyboard-tab
date: 2025-12-17T11:26:57Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, storyboard]
related_paths:
  - ai-pic-frontend/src/app/scripts/[id]/page.tsx
summary: "Removed inline storyboard workspace from script detail page; direct users to the dedicated storyboard page."
---

## User Prompt
http://localhost:8089/scripts/b40daa0d5f9848e0ae6c90bc02d7bb45 这个页面的分镜工作台的内容去掉吧，直接跳到专门的分镜管理

## Goals
- Remove the embedded storyboard workspace from the script detail page and guide users to the standalone storyboard page.

## Changes
- Dropped the storyboard tab/states/logic from `scripts/[id]` page; retained only overview and scene tabs.
- Kept a single “打开分镜管理”跳转按钮（episodes/<id>/storyboard）without rendering storyboard data locally.
- Cleaned unused imports/state and related helpers.

## Validation
- `npm run lint` (frontend) — pass.
- Manual browser check pending (page should now only show概览/场景 tabs; storyboard content removed).

## Next Steps
- After login, confirm the script page shows only two tabs and the storyboard link navigates to the dedicated storyboard page.

## Linked Commits
- (pending)
