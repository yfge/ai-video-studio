---
id: 2026-05-25T09-30-17Z-timeline-clip-rework-controls
date: "2026-05-25T09:30:17Z"
participants: [human, codex]
models: [gpt-5]
tags: [frontend, timeline, media-assets, rework]
related_paths:
  - ai-pic-frontend/src/components/features/episode/EpisodeTimelineWorkspace.tsx
  - ai-pic-frontend/src/components/features/episode/TimelineClipAssetAuditPanel.tsx
  - ai-pic-frontend/src/components/features/episode/TimelineClipReworkControls.tsx
  - ai-pic-frontend/src/utils/api/endpoints/timeline.endpoints.ts
  - ai-pic-frontend/src/utils/api/types/timeline.types.ts
  - ai-pic-frontend/tests/timelineClipReworkControls.test.ts
  - docs/exec-plans/active/main-chain-commercial-readiness.md
  - docs/exec-plans/active/timeline-main-chain-optimization.md
  - tasks.md
summary: "Wire operator rework controls to stable clip asset API"
---

## User Prompt

connit 然后继续

使用你的内置浏览器

## Goals

- Continue Phase 5 after the operator asset audit read view landed.
- Add a narrow operator control surface for the existing stable `clip_id`
  rework API.
- Keep this commit scoped to recording existing `media_asset_id` replacement
  lineage; do not claim real provider generation or render queue orchestration.

## Changes

- Added `timelineAPI.reworkTimelineClip` and frontend request/action types for
  `POST /api/v1/timelines/{timeline_id}/clips/{clip_id}/rework`.
- Added `TimelineClipReworkControls` under the selected clip asset audit panel.
  Operators can choose re-dub, re-cut, or re-render, enter an existing
  `media_asset_id`, optionally set an asset role and reason, then refresh the
  asset audit view after a successful record.
- Added a focused frontend test for compact rework payload construction.
- Updated `tasks.md` and active execution plans to mark existing-media operator
  rework controls as done while leaving real provider-backed rework
  orchestration pending.

## Validation

- `cd ai-pic-frontend && npm run test`: passed, 17 tests.
- `cd ai-pic-frontend && npm run lint`: passed with 0 errors and 18 existing
  warnings.
- Codex in-app browser validation opened
  `http://localhost:3090/episodes/133/workspace?tab=timeline&scriptId=117` and
  confirmed the selected clip inspector shows the asset audit panel, rework
  action labels, `media_asset_id` input, reason input, and enabled
  `记录重做资产` button after local form input.
- Browser evidence:
  `artifacts/runs/frontend-clip-rework-controls-iab-20260525T092838Z/browser-validation.json`
  and
  `artifacts/runs/frontend-clip-rework-controls-iab-20260525T092838Z/timeline-clip-rework-controls.png`.
- Browser validation did not submit the rework form, so no local development DB
  lineage row was created by this check.
- `python scripts/check_repo_docs.py`: passed.
- `python scripts/check_repo_contracts.py --mode audit`: passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>`: passed.
- `git diff --check`: passed.
- `cd ai-pic-frontend && npx prettier --write <changed frontend/docs/ledger files>`:
  passed; staged pre-commit also ran prettier.
- `SKIP=backend-pytest pre-commit run --files <staged files>`: passed after
  prettier hook formatting. `backend-pytest` was skipped because this commit
  changes frontend/docs/ledger only; affected behavior is covered by frontend
  lint, tests, and in-app browser validation.
- `cd ai-pic-frontend && npm run build` was not run because this change stays
  inside existing client components, a feature hook-free API client wrapper, and
  tests; it does not touch routes, layouts, auth, config, or SSR-sensitive code.

## Next Steps

- Add provider-backed rework generation for selected Timeline clips.
- Persist generated video/audio outputs as media assets and replacement lineage
  without changing stable `clip_id`.
- Wire successful re-render output back into the render/export queue.

## Linked Commits

- Pending.
