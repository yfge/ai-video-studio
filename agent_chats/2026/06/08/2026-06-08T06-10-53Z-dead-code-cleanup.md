---
id: 2026-06-08T06-10-53Z-dead-code-cleanup
date: "2026-06-08T06:10:53Z"
participants:
  - user
  - codex
models:
  - GPT-5 Codex
tags:
  - frontend
  - dead-code
  - cleanup
related_paths:
  - ai-pic-frontend/src/components/features/storyboard/StoryboardEditor.js
  - ai-pic-frontend/src/components/features/environments/EnvironmentCreateIcon.tsx
  - ai-pic-frontend/src/components/features/environments/EnvironmentDetailHeader.tsx
  - ai-pic-frontend/src/components/features/hooks/AdSnippetCard.tsx
  - ai-pic-frontend/src/components/features/hooks/HookPlanPanel.tsx
  - ai-pic-frontend/src/components/features/hooks/HookTagBadge.tsx
  - ai-pic-frontend/src/components/features/StoryboardFrameCard.tsx
  - ai-pic-frontend/src/components/shared/modals/AlertModalProvider.tsx
  - ai-pic-frontend/src/components/shared/modals/UserDetailsModal.tsx
  - ai-pic-frontend/tests/storyboardStructure.e2e.tsx
  - ai-pic-frontend/tests/virtualIPImageGrid.test.tsx
  - ai-pic-frontend/tests/workspaceStoryboardTabContent.test.tsx
  - ai-pic-frontend/src/utils/storyboardToggle.js
  - ai-pic-frontend/tests/storyboardToggle.test.js
summary: Removed unreferenced legacy frontend files and stale React default imports.
---

## User Prompt

/goal 清理系统中旧的死代码

## Goals

- Identify dead-code candidates from current repository references rather than historical assumptions.
- Remove only low-risk frontend code that has no current imports, routes, or tests depending on it.
- Keep existing dirty worktree changes untouched.

## Changes

- Deleted the legacy `StoryboardEditor.js` component after confirming no current route or component imports it and the workspace route now owns storyboard UI.
- Deleted unused environment helper components that are not exported by the environment feature barrel and are not imported by current environment pages.
- Deleted the old storyboard toggle helper and its self-contained unit test after confirming no production code references it.
- Removed stale default `React` imports reported by `tsc --noUnusedLocals` from clean frontend source and test files.

## Validation

- `cd ai-pic-frontend && npm exec -- tsc --noEmit --noUnusedLocals --noUnusedParameters --pretty false`: failed only on pre-existing untracked `tests/timelineWorkspaceLayout.test.tsx` unused `React` import, which this cleanup intentionally did not edit.
- `cd ai-pic-frontend && npm run lint`: passed with 4 existing warnings and 0 errors.
- `cd ai-pic-frontend && npm run test`: passed, 39 tests after deleting the obsolete storyboard toggle test.
- `python scripts/check_repo_docs.py`: passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>`: passed.
- `pre-commit run --files <changed files>`: passed.

## Next Steps

- Keep investigating larger backend legacy areas separately; many are scripts or compatibility surfaces and need deeper runtime proof before deletion.

## Linked Commits

- Pending.
