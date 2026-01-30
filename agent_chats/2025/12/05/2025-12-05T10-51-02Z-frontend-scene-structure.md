---
id: 2025-12-05T10-51-02Z-frontend-scene-structure
date: 2025-12-05T10:51:02Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, story-structure]
related_paths:
  - ai-pic-frontend/src/app/scripts/[id]/page.tsx
  - ai-pic-frontend/src/components/SceneStructurePanel.tsx
  - ai-pic-frontend/src/utils/api.ts
  - ai-pic-frontend/src/app/register/page.tsx
  - task.md
summary: "Wire scene/beat/shot UI into script detail with permission guard and clean lint warnings"
---

## User Prompt

继续

## Goals

- Expose structured scenes/beats/shots on the script detail page with editing gated by admin roles.
- Ensure supporting API helpers and registration flow pass lint, and keep the task board in sync.

## Changes

- Added `SceneStructurePanel` to the script detail scenes tab with admin-only editing, using live structure APIs.
- Fetched current user for permission checks, expanded API client helpers, and tightened typings to remove `any` usage.
- Fixed register page error handling type, cleaned up unused variables, and updated the task board to mark frontend sync done.

## Validation

- npm run lint

## Next Steps

- Extend UI error/permission messaging and align storyboard view with structured scene data.
- Add end-to-end tests covering scene/beat/shot CRUD and permissions.

## Linked Commits

- (pending)
