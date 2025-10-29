---
id: 2025-10-29T07-42-00Z-admin-user-flow-cleanup
date: 2025-10-29T07:42:00Z
participants: [human, codex]
models: [gpt-5-codex]
tags: [frontend, admin]
related_paths:
  - ai-pic-frontend/src/app/admin/users/page.tsx
  - ai-pic-frontend/src/components/AdminLayout.tsx
  - ai-pic-frontend/src/components/UserDetailsModal.tsx
summary: "Simplified admin user hooks and aligned details modal with alert modal conventions"
---

## User Prompt
检查tasks.md 规划下一步的工作；及时提交现有更改，保持最小原子提交。

## Goals
- Remove unused approval helpers and ensure admin effects use stable callbacks.
- Align user details modal with the new `AlertModalProvider` confirm patterns.
- Clean up admin layout imports after refactoring approval workflow.

## Changes
- Converted user list loaders to `useCallback` and dropped unused approval handler state.
- Updated `UserDetailsModal` to memoize audit log fetches and work with alert-based confirmations.
- Removed stale imports from `AdminLayout` after role/approval cleanups.

## Validation
- npm run lint

## Next Steps
- Explore consolidating admin modal types with the shared API interfaces to avoid duplicate shapes.

## Linked Commits
N/A
