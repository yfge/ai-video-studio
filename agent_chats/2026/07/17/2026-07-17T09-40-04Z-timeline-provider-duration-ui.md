## User Prompt

Remove arbitrary Timeline video-duration input, show the Timeline target as read-only, stop sending manual duration, and keep legacy clip deep links working after video-window aggregation.

## Goals

- Make the Timeline clip duration visibly authoritative in the Provider generation panel.
- Remove manual duration state and payload fields from the frontend.
- Resolve absorbed legacy clip IDs to their new grouped video window.
- Prove the current Timeline 76 workspace renders the new 10-shot layout.

## Changes

- Replaced the numeric duration input with `Timeline 目标 X 秒，Provider 自动适配并裁切`.
- Removed duration parsing, validation, component state, callbacks, and task payload serialization.
- Added deep-link matching for top-level and `source_refs.source_clip_ids` aliases.
- Added focused rendering/payload/deep-link coverage.

## Validation

- `npm run lint`: passed with 0 errors and 3 existing warnings.
- `npx tsx --test tests/timelineClipReworkControls.test.ts tests/timelineWorkspaceLayout.test.tsx`: 69 passed.
- Full `npm test` was attempted in the clean patched worktree and was blocked by nine pre-existing Canvas failures in `ProductionCanvasChatBar` and `ProductionCanvasPlanner`; no Timeline test failed.
- Browser evidence: `artifacts/runs/timeline-window-v2-20260717T174300/` shows 10 video clips over 01:00, preserves the requested first-clip deep link, and renders `Timeline 目标 6.39 秒，Provider 自动适配并裁切` with no legacy duration input.
- Chrome DevTools transport timed out; the repository harness recorded a successful Playwright fallback, Network responses, Console output, DOM snapshot, and screenshot. The only observed 404 was the pre-existing missing environment image.

## Next Steps

- None.

## Linked Commits

- This frontend commit.
