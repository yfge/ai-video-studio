---
id: 2025-12-11T05-12-41Z-remove-gallery-and-align-tasks-nav
date: 2025-12-11T05:12:41Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, navigation]
related_paths:
  - ai-pic-frontend/src/app/gallery/page.tsx
  - ai-pic-frontend/src/app/tasks/page.tsx
  - ai-pic-frontend/src/app/page.tsx
summary: "Remove the gallery page and make the tasks management page use the shared Navigation header like other views."
---

## User Prompt

- “图片画廊页面也干掉，同时任务 管理使用和其他页面一样的导航”

## Goals

- Remove the standalone image gallery page and any navigation that points to it.
- Make the `/tasks` page use the same top-level `Navigation` component as the rest of the app instead of a custom header.

## Changes

- Deleted `src/app/gallery/page.tsx`, removing the gallery page route and its custom header.
- Updated the home page (`src/app/page.tsx`) to drop the CTA button linking to `/gallery`.
- Refactored `src/app/tasks/page.tsx` to:
  - Import and render the shared `Navigation` component at the top.
  - Remove the inline header/nav with `Link` to `/tasks` and `/gallery`.
  - Keep the task list layout, auto-refresh toggle, and start/delete actions under the common layout.

## Validation

- `cd ai-pic-frontend && npm run lint`

## Next Steps

- If a gallery-like view is needed later, reintroduce it with real backend data and reuse the common navigation instead of a custom header.

## Linked Commits

- pending
