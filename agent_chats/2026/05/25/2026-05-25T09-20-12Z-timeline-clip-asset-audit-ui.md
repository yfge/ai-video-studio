---
id: 2026-05-25T09-20-12Z-timeline-clip-asset-audit-ui
date: "2026-05-25T09:20:12Z"
participants: [human, codex]
models: [gpt-5]
tags: [frontend, timeline, media-assets, operator-ui]
related_paths:
  - ai-pic-frontend/src/components/features/episode/EpisodeTimelineWorkspace.tsx
  - ai-pic-frontend/src/components/features/episode/EpisodeTimelineMainPanel.tsx
  - ai-pic-frontend/src/components/features/episode/TimelineClipAssetAuditPanel.tsx
  - ai-pic-frontend/src/components/features/episode/useTimelineClipAssets.ts
  - ai-pic-frontend/src/utils/api/endpoints/timeline.endpoints.ts
  - ai-pic-frontend/src/utils/api/types/timeline.types.ts
  - docs/exec-plans/active/main-chain-commercial-readiness.md
  - docs/exec-plans/active/timeline-main-chain-optimization.md
  - tasks.md
summary: "Show selected Timeline clip asset audit in operator workspace"
---

## User Prompt

connit 然后继续

你可以使用chrome mcp

使用你的内置浏览器

## Goals

- Continue Phase 5 after the stable `clip_id` rework API landed.
- Add an operator read-side view for selected Timeline clip asset lineage.
- Keep scope limited to asset audit visibility, not real provider generation or
  render queue orchestration.
- Validate the user-visible path with the Codex in-app browser after Chrome MCP
  was unavailable.

## Changes

- Added frontend Timeline clip asset API types and a `listTimelineClipAssets`
  client wrapper for `GET /api/v1/timelines/{timeline_id}/clip-assets`.
- Added `useTimelineClipAssets` to load assets for the selected Timeline version
  and refresh after render job status changes.
- Added `TimelineClipAssetAuditPanel` to show selected clip source/output asset
  roles, locators, source labels, render job links, and replacement history.
- Extracted the Timeline main canvas into `EpisodeTimelineMainPanel` to keep
  `EpisodeTimelineWorkspace.tsx` below the file-size threshold while adding the
  inspector audit panel.
- Updated `tasks.md` and active execution plans to mark only the operator
  read-side asset audit view as done, leaving real rework orchestration and
  production sample validation pending.

## Validation

- `cd ai-pic-frontend && npm run lint`: passed with 0 errors and 18 existing
  warnings.
- `cd ai-pic-frontend && npm run test`: passed, 16 tests.
- Chrome DevTools MCP was attempted first, but `127.0.0.1:9222/json/version`
  returned HTTP 404 from an existing Chrome listener and a separate Chrome could
  not bind the same port; no Chrome MCP verification is claimed.
- Local dev DB migration was applied for browser validation:
  `docker exec ai-video-backend sh -lc 'cd /app/ai-pic-backend && alembic upgrade head'`.
- Codex in-app browser validation logged in as `geyunfei`, opened
  `http://localhost:3090/episodes/133/workspace?tab=timeline&scriptId=117`,
  and confirmed the asset audit panel and empty asset state were visible.
- Browser evidence:
  `artifacts/runs/frontend-clip-asset-audit-iab-real-20260525T091453Z/browser-validation.json`
  and
  `artifacts/runs/frontend-clip-asset-audit-iab-real-20260525T091453Z/timeline-clip-asset-audit-real.png`.
- Backend access logs during browser validation included
  `GET /api/v1/timelines/2/clip-assets?timeline_version=1` returning 200.
- `python scripts/check_repo_docs.py`: passed.
- `python scripts/check_repo_contracts.py --mode audit`: passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>`: passed.
- `git diff --check`: passed.
- `cd ai-pic-frontend && npx prettier --write <changed frontend/docs/ledger files>`:
  passed with no changes.
- `SKIP=backend-pytest pre-commit run --files <staged files>`: passed.
  `backend-pytest` was skipped because this commit changes frontend/docs/ledger
  only; affected frontend behavior is covered by lint, tests, and in-app browser
  validation.

## Next Steps

- Wire rework requests into real provider generation and render queue
  orchestration.
- Backfill or regenerate real `timeline_clip_assets` rows for legacy Timelines
  when sample production needs non-empty lineage on older data.
- Continue the 10 narrow vertical sample production validation.

## Linked Commits

- Pending.
