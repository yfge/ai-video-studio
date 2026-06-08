---
id: 2026-06-08T09-43-29Z-frontend-type-export-cleanup
date: "2026-06-08T09:43:29Z"
participants:
  - user
  - codex
models:
  - GPT-5 Codex
tags:
  - frontend
  - types
  - dead-code
related_paths:
  - ai-pic-frontend/src/components/features/episode/EpisodeTimelineRenderModel.ts
  - ai-pic-frontend/src/components/features/episode/EpisodeWorkflowSteps.tsx
  - ai-pic-frontend/src/components/features/episode/WorkspaceScriptTabContentModel.ts
  - ai-pic-frontend/src/components/shared/modals/image-to-image/types.ts
  - ai-pic-frontend/src/utils/api/types
summary: Removed or privatized unused frontend exported types while preserving active response shapes.
---

## User Prompt

Continue goal: `清理项目的死代码，直到没有`

## Goals

- Clear the remaining `knip` unused exported type findings that are safe to handle independently.
- Preserve active data shapes by making nested helper types private instead of deleting them when still referenced internally.
- Delete only type declarations with no current source references.

## Changes

- Made component-local helper types private where only their declaring file uses them.
- Made nested API response helper types private while keeping the top-level imported response/request interfaces exported.
- Removed orphaned historical type declarations that had no current source references.
- Removed now-unused imports left behind by deleting `SceneStructureMaps`.

## Validation

- `npm exec tsc -- --noEmit --noUnusedLocals --noUnusedParameters --pretty false`
- `npm run lint`
- `npm run test`
- `npm exec --package=knip -- knip --no-progress`
- `python scripts/check_repo_docs.py`
- `python scripts/check_repo_contracts.py --mode diff <changed files>`
- `git diff --check -- <changed files>`
- `pre-commit run --files <staged files>`
- Result: typecheck, lint, tests, docs, contracts, whitespace, and pre-commit passed; lint kept 4 existing warnings; knip decreased to 1 unused export and 1 unused exported type.

## Next Steps

- Remaining `knip` findings are `hexToAudioUrl` in `useVirtualIPDetail.ts` and `StoryboardGridPanel` in oversized `WorkspaceStoryboardSupportModel.ts`; both need dedicated file-size-contract-safe cleanup.

## Linked Commits

- This commit: `chore(frontend): remove unused type exports`.
