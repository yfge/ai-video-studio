# Frontend

## Default Path

- Operator default path is moving toward `Episode -> Timeline`.
- Storyboard remains a support surface, not the long-term orchestration center.

## Structure Rules

- Pages should stay below 200 lines where practical.
- Feature state should move into hooks before pages grow further.
- Shared API access goes through `src/utils/api/client.ts`, `src/hooks/useApi.ts`, or endpoint barrels.

## Harness Notes

- API clients attach `X-Harness-Run-ID` and `X-Client-Request-ID`.
- Browser scenarios are defined in `scripts/harness/scenarios.py`.
- Frontend validation minimum is `npm run lint`; add `npm run test` for behavior changes and `npm run build` for route/layout/auth changes.

## Active Debt

- `src/app/episodes/[id]/storyboard/page.tsx` remains far above the target size.
- Some shared modals still exceed the preferred size limit.
- Browser scenario coverage is foundational, not complete; see `QUALITY_SCORE.md`.
