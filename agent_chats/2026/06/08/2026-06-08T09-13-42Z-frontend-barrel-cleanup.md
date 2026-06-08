---
id: 2026-06-08T09-13-42Z-frontend-barrel-cleanup
date: "2026-06-08T09:13:42Z"
participants:
  - user
  - codex
models:
  - GPT-5 Codex
tags:
  - frontend
  - dead-code
  - exports
related_paths:
  - ai-pic-frontend/src/components/features/index.ts
  - ai-pic-frontend/src/components/features/episode/index.ts
  - ai-pic-frontend/src/components/shared/modals/index.ts
  - ai-pic-frontend/src/components/shared/operator/index.ts
  - ai-pic-frontend/src/components/ui/index.ts
summary: Removed unused frontend barrel exports and small barrel files with no import sources.
---

## User Prompt

Continue goal: `清理项目的死代码，直到没有`

## Goals

- Continue reducing frontend export-level dead code.
- Keep route-consumed barrels intact while removing symbols with no consumers.
- Delete small barrel files that are only reachable from another barrel and have no direct import source.

## Changes

- Reduced the top-level features barrel to symbols used by current routes and components.
- Reduced the episode barrel to the symbols imported by the episode workspace route.
- Deleted unused `stories`, `story-detail`, `virtual-ip`, and `virtual-ip-images` barrel files.
- Removed unused modal, operator, and UI barrel exports while keeping active imports intact.
- Deleted unused `StoryboardVideoModal`, removed unused `OperatorDrawer`, and made storyboard card helpers private.

## Validation

- `rg -n "from ['\"]@/components/features['\"]|from ['\"]@/components/features/episode['\"]|from ['\"]@/components/shared/modals['\"]|from ['\"]@/components/ui['\"]" ai-pic-frontend/src ai-pic-frontend/tests`
- `npm exec tsc -- --noEmit --noUnusedLocals --noUnusedParameters --pretty false`
- `npm run lint`
- `npm run test`
- `npm exec --package=knip -- knip --no-progress` (remaining export/type findings expected; no unused files left from this batch)
- `python scripts/check_repo_docs.py`
- `python scripts/check_repo_contracts.py --mode diff <changed files>`
- `pre-commit run --files <staged files>`

## Next Steps

- Continue remaining export/type cleanup from modules that are not public route entrypoints.
- Avoid deleting implementation files when the unused finding is only an unused barrel re-export.

## Linked Commits

- This commit: `chore(frontend): prune unused barrels`.
