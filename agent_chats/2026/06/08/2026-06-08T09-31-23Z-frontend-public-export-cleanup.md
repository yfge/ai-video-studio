---
id: 2026-06-08T09-31-23Z-frontend-public-export-cleanup
date: "2026-06-08T09:31:23Z"
participants:
  - user
  - codex
models:
  - GPT-5 Codex
tags:
  - frontend
  - api-client
  - dead-code
related_paths:
  - ai-pic-frontend/src/utils/api/client.ts
  - ai-pic-frontend/src/utils/api/trace.ts
  - ai-pic-frontend/src/components/shared/index.ts
  - ai-pic-frontend/src/components/shared/MarketingFields.tsx
  - ai-pic-frontend/src/components/shared/StyleSpecAdvancedPanel.tsx
  - ai-pic-frontend/src/utils/modelUi.ts
  - ai-pic-frontend/src/utils/modelUiImage.ts
  - ai-pic-frontend/src/utils/routes.ts
summary: Removed unused frontend public exports while preserving internal implementation and active imports.
---

## User Prompt

Continue goal: `清理项目的死代码，直到没有`

## Goals

- Reduce remaining frontend unused export findings from `knip`.
- Avoid changing API endpoint compatibility exports in this batch.
- Keep active frontend behavior unchanged by only removing or privatizing unreferenced public exports.

## Changes

- Removed the unused `http` shortcut object from `utils/api/client.ts`; current code imports `httpClient` directly.
- Made trace helper functions private inside `utils/api/trace.ts` while keeping `applyTraceHeaders` and `readTraceHeaders` exported for the API client.
- Removed unused shared barrel type re-exports for marketing, advanced image fields, and style spec keys.
- Made `MarketingFormValues`, `StyleSpecKey`, `ImageUiOptions`, and `EpisodeWorkspaceTab` private implementation details where they have no external imports.

## Validation

- `rg` checks for removed export names across frontend source and tests.
- `npm exec tsc -- --noEmit --noUnusedLocals --noUnusedParameters --pretty false`
- `npm run lint`
- `npm run test`
- `npm exec --package=knip -- knip --no-progress`
- `python scripts/check_repo_docs.py`
- `python scripts/check_repo_contracts.py --mode diff <changed files>`
- `git diff --check -- <changed files>`
- `pre-commit run --files <staged files>`
- Result: typecheck, lint, tests, docs, contracts, whitespace, and pre-commit passed; lint kept 4 existing warnings; knip decreased to 80 unused exports and 39 unused exported types.

## Next Steps

- Continue from remaining API endpoint and exported type findings after this batch lands.
- Treat endpoint named exports separately because existing tests preserve legacy compatibility exports.

## Linked Commits

- This commit: `chore(frontend): remove unused public exports`.
