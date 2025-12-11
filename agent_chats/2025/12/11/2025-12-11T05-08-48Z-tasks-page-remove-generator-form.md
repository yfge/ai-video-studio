---
id: 2025-12-11T05-08-48Z-tasks-page-remove-generator-form
date: 2025-12-11T05:08:48Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, tasks]
related_paths:
  - ai-pic-frontend/src/app/tasks/page.tsx
summary: "Remove the generation configuration form from the tasks management page and keep a clean task list view."
---

## User Prompt

- “把任务 管理中的生成配置整体 去掉，同时列”

## Goals

- Remove the generation configuration panel from the `/tasks` page so that the view focuses purely on listing and managing existing tasks.
- Preserve task listing, status display, and start/delete actions.

## Changes

- Rewrote `src/app/tasks/page.tsx` to:
  - Drop the entire left-side generation configuration form, image gallery selectors, and related state.
  - Keep the header, navigation, polling toggle, and task list card.
  - Render the task list full-width with status badges, timestamps, and delete/start controls.
- Simplified imports to only what is needed for listing and managing tasks.

## Validation

- `cd ai-pic-frontend && npm run lint`

## Next Steps

- If needed, reintroduce task creation in a dedicated flow (e.g., separate page or modal) without cluttering the management list.

## Linked Commits

- pending

