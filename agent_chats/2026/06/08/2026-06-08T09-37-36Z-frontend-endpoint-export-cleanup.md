---
id: 2026-06-08T09-37-36Z-frontend-endpoint-export-cleanup
date: "2026-06-08T09:37:36Z"
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
  - ai-pic-frontend/src/hooks/useEpisodeCharacters.ts
  - ai-pic-frontend/src/utils/api/endpoints
  - ai-pic-frontend/src/utils/api/types
summary: Narrowed API endpoint public exports to namespace objects and removed the unused story novel endpoint surface.
---

## User Prompt

Continue goal: `清理项目的死代码，直到没有`

## Goals

- Remove unused named endpoint exports reported by `knip`.
- Preserve the active frontend API calling convention through `*API` namespace objects.
- Keep the `script/audio.endpoints` legacy compatibility exports unchanged because tests explicitly protect them.

## Changes

- Converted implementation functions in active endpoint modules from named public exports to file-private functions.
- Updated `useEpisodeCharacters` to consume `episodeCharacterAPI` instead of directly importing episode-character functions.
- Removed the unused story novel endpoint module and its isolated frontend type definitions.
- Removed story novel endpoint/type barrel exports.
- Made `getAuthToken` private and removed the now-unused API base constant from common frontend API types.

## Validation

- `rg` checks for remaining endpoint named exports and story-novel references.
- `npm exec tsc -- --noEmit --noUnusedLocals --noUnusedParameters --pretty false`
- `npm run lint`
- `npm run test`
- `npm exec --package=knip -- knip --no-progress`
- `python scripts/check_repo_docs.py`
- `python scripts/check_repo_contracts.py --mode diff <changed files>`
- `git diff --check -- <changed files>`
- `pre-commit run --files <staged files>`
- Result: typecheck, lint, tests, docs, contracts, whitespace, and pre-commit passed; lint kept 4 existing warnings; knip decreased to 1 unused export and 39 unused exported types.

## Next Steps

- Continue with the remaining non-endpoint exported types and the oversized `useVirtualIPDetail.ts` finding.
- Keep endpoint compatibility tests intact unless a dedicated API surface change removes those legacy contracts.

## Linked Commits

- This commit: `chore(frontend): narrow endpoint exports`.
