---
id: 2026-06-08T09-08-55Z-frontend-export-surface-cleanup
date: "2026-06-08T09:08:55Z"
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
  - ai-pic-frontend/src/components/features/episode
  - ai-pic-frontend/src/app/virtual-ip/[id]/VirtualIPDetailPageParts.tsx
  - ai-pic-frontend/src/components/features/index.ts
summary: Removed unused frontend component exports and narrowed internal helpers that had no external consumers.
---

## User Prompt

Continue goal: `清理项目的死代码，直到没有`

## Goals

- Continue reducing frontend dead-code findings after file-level cleanup.
- Remove component files that were only reachable through unused barrel exports.
- Narrow helpers that are used only inside their declaring module.
- Delete an unused Timeline clip helper with no repository call sites.

## Changes

- Removed unused `EpisodeAspectRatioSelect` and `ScriptList` component files.
- Removed their re-exports from episode and feature barrels.
- Converted internal-only helpers from exported functions to private functions.
- Removed the unused `timelineClipGridPanelIndex()` helper.
- Removed unused `EpisodeTimelineInspectorContent` and its private inspector row/imports.

## Validation

- `rg -n "EpisodeAspectRatioSelect|ScriptList|ReadinessRow|timelineSceneNumber|legacyAudioTimelineToTimelineTracks|ContextRow|InspectorRow|EpisodeTimelineInspectorContent|timelineClipGridPanelIndex" ai-pic-frontend/src ai-pic-frontend/tests scripts docs`
- `npm exec tsc -- --noEmit --noUnusedLocals --noUnusedParameters --pretty false`
- `npm run lint`
- `npm run test`
- `npm exec --package=knip -- knip --no-progress`
- `python scripts/check_repo_docs.py`
- `python scripts/check_repo_contracts.py --mode diff <changed files>`
- `pre-commit run --files <staged files>`

## Next Steps

- Continue reviewing remaining export/type-level findings with direct usage proof.
- Treat docs-only mentions and active plan references as context, not proof that an export is live.

## Linked Commits

- This commit: `chore(frontend): narrow unused exports`.
