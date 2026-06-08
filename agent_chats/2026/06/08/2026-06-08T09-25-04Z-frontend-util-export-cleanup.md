---
id: 2026-06-08T09-25-04Z-frontend-util-export-cleanup
date: "2026-06-08T09:25:04Z"
participants:
  - user
  - codex
models:
  - GPT-5 Codex
tags:
  - frontend
  - utils
  - dead-code
related_paths:
  - ai-pic-frontend/src/utils/auth.ts
  - ai-pic-frontend/src/utils/aspectRatios.ts
  - ai-pic-frontend/src/utils/marketingTemplates.ts
summary: Removed unused frontend utility exports while preserving currently imported helpers.
---

## User Prompt

Continue goal: `清理项目的死代码，直到没有`

## Goals

- Continue reducing frontend utility export dead code.
- Remove unused localStorage auth helpers that no current route or component imports.
- Keep utility constants and types private when only used inside the declaring module.

## Changes

- Removed unused auth helpers and color/status-role exports from `utils/auth.ts`.
- Made `formatDateTime` private because only `formatRelativeTime` uses it.
- Made `ALLOWED_ASPECT_RATIOS` private inside `utils/aspectRatios.ts`.
- Made marketing template helper types private inside `utils/marketingTemplates.ts`.

## Validation

- `rg -n "\\b(getCurrentUser|getAuthToken|clearAuth|redirectToLogin|requireAuth|isSuperUser|isActiveUser|getUserStatusColor|getUserRoleColor|formatDateTime|ALLOWED_ASPECT_RATIOS|HookBeat|HookPlan|AdSnippet)\\b" ai-pic-frontend/src ai-pic-frontend/tests`
- `npm exec tsc -- --noEmit --noUnusedLocals --noUnusedParameters --pretty false`
- `npm run lint`
- `npm run test`
- `npm exec --package=knip -- knip --no-progress`
- `python scripts/check_repo_docs.py`
- `python scripts/check_repo_contracts.py --mode diff <changed files>`
- `pre-commit run --files <staged files>`
- Result: typecheck, lint, tests, docs, contracts, whitespace, and pre-commit passed; lint kept 4 existing warnings; knip decreased to 84 unused exports and 45 unused exported types.

## Next Steps

- Continue from the remaining API endpoint and type export findings.
- Avoid pruning auth helpers that are still imported by admin shells, guards, or rows.

## Linked Commits

- This commit: `chore(frontend): remove unused util exports`.
