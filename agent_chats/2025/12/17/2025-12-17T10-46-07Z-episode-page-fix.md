---
id: 2025-12-17T10-46-07Z-episode-page-fix
date: 2025-12-17T10:46:07Z
participants: [human, codex]
models: [gpt-4o-mini]
tags: [frontend, bugfix]
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/page.tsx
summary: "Fix client runtime errors on episode page (duplicate declarations, missing useMemo import) causing white screen."
---

## User Prompt

http://localhost:8089/episodes/cd378417b7f143eab5bc6d063cd7f6e7 白屏

## Goals

- Resolve client-side exception/500 on episode page so it renders again.

## Changes

- Removed duplicate declarations of episode/storyboard/timeline variables introduced during timeline work.
- Added missing `useMemo` import so hooks resolve at runtime; kept single source of timeline tracks/range.

## Validation

- `npm run lint` (frontend) — pass.
- Docker frontend logs now show `/episodes/<biz>` 200; page still requires login to view, but runtime hook errors are cleared.

## Next Steps

- Re-login and confirm episode page renders with timeline UI; monitor for residual 404 `_next/webpack-hmr` (dev-only).

## Linked Commits

- (pending)
