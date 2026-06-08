---
id: 2026-06-08T09-03-10Z-frontend-dead-file-cleanup
date: "2026-06-08T09:03:10Z"
participants:
  - user
  - codex
models:
  - GPT-5 Codex
tags:
  - frontend
  - dead-code
  - tests
related_paths:
  - ai-pic-frontend/src/components/features/hooks
  - ai-pic-frontend/src/hooks
  - ai-pic-frontend/tests/storyboardStructure.test.tsx
summary: Removed frontend files with no import entrypoint and made a dormant storyboard UI test discoverable by the existing test runner.
---

## User Prompt

Continue goal: `清理项目的死代码，直到没有`

## Goals

- Continue whole-repository dead-code cleanup with import/export evidence.
- Remove frontend files that are not reachable from application or test entrypoints.
- Preserve useful dormant test coverage by making it discoverable instead of deleting it.
- Leave unrelated in-progress frontend changes untouched.

## Changes

- Removed unused hook-panel components that were only referenced by their own unused barrel.
- Removed unused generic hook helpers that were only exported from an unused `src/hooks` barrel.
- Removed duplicate default exports from components that are consumed through named imports.
- Removed unused direct frontend dev dependencies and a PostCSS JSDoc type import that implied an unlisted dependency.
- Renamed `storyboardStructure.e2e.tsx` to `storyboardStructure.test.tsx` so the existing `npm run test` glob runs it.

## Validation

- `npm run lint`
- `npm exec tsc -- --noEmit --noUnusedLocals --noUnusedParameters --pretty false`
- `npm exec --package=knip -- knip --no-progress`
- `npm exec tsx -- --test tests/storyboardStructure.test.tsx`
- `npm run test`
- `python scripts/check_repo_docs.py`
- `python scripts/check_repo_contracts.py --mode diff <changed files>`
- `pre-commit run --files <staged files>`

## Next Steps

- Continue reducing remaining `knip` export-level noise with call-chain proof.
- Do not remove files or exports that are reachable through app routes, direct component imports, or harness entrypoints.

## Linked Commits

- This commit: `chore(frontend): remove dead frontend helpers`.
