---
id: 2026-06-08T09-20-21Z-frontend-hook-export-cleanup
date: "2026-06-08T09:20:21Z"
participants:
  - user
  - codex
models:
  - GPT-5 Codex
tags:
  - frontend
  - hooks
  - dead-code
related_paths:
  - ai-pic-frontend/src/hooks/episodeDetailUtils.ts
  - ai-pic-frontend/src/hooks/useEpisodeDetail.ts
  - ai-pic-frontend/src/hooks/useStoryDetail.ts
  - ai-pic-frontend/src/hooks/useImageGenProfiles.ts
  - ai-pic-frontend/src/hooks/useStylePresets.ts
  - ai-pic-frontend/src/hooks/useStyleSchema.ts
  - ai-pic-frontend/src/hooks/useVirtualIPDetail.ts
summary: Removed unused frontend hook helper exports and a stale story detail utility module.
---

## User Prompt

Continue goal: `清理项目的死代码，直到没有`

## Goals

- Continue reducing frontend export-level dead code.
- Remove hook helpers that have no repository consumers.
- Keep hook behavior unchanged where helpers are still used internally.

## Changes

- Removed unused `getNumber`, `extractScenes`, and `getSceneCount` exports from episode detail helpers.
- Removed the stale `storyDetailUtils` module and its unused re-exports.
- Removed unused cache-clear exports for image generation profiles, style presets, and style schema.

## Validation

- `rg -n "\\b(getNumber|extractScenes|getSceneCount|extractEpisodeScenes|getEpisodeSceneCount|clearImageGenProfilesCache|clearStylePresetsCache|clearStyleSchemaCache)\\b" ai-pic-frontend/src ai-pic-frontend/tests`
- `npm exec tsc -- --noEmit --noUnusedLocals --noUnusedParameters --pretty false`
- `npm run lint`
- `npm run test`
- `npm exec --package=knip -- knip --no-progress`
- `python scripts/check_repo_docs.py`
- `python scripts/check_repo_contracts.py --mode diff <changed files>`
- `pre-commit run --files <staged files>`

## Next Steps

- Continue from the remaining `knip` export/type findings.
- Treat API endpoint compatibility exports separately from local hook helper exports.

## Linked Commits

- This commit: `chore(frontend): remove unused hook exports`.
