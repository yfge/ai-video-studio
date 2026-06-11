## User Prompt

PLEASE IMPLEMENT THIS PLAN: 剧集与分镜视频可见性优化方案。

## Goals

- Add a Timeline-first resolved video read model so frontend surfaces stop guessing clip video URLs independently.
- Show playable videos inline on the Timeline selected clip surface, storyboard support rows, and succeeded render output area.
- Preserve storyboard as a support view for Timeline video clips, not a new episode-wide storyboard orchestration center.

## Changes

- Added `GET /api/v1/timelines/{timeline_id}/resolved-videos` through a thin router, schema, and service.
- The service reads accessible timelines, reuses the render worker `TimelineClipResolver`, and overlays active clip tasks as `generating`.
- Added frontend API types, `timelineAPI.listTimelineResolvedVideos()`, and `useTimelineResolvedVideos()`.
- Rewired Timeline render readiness, workspace production state, selected clip production summary, storyboard clip management, and render output panel to consume the resolved read model.
- Added inline `<video controls preload="none">` players for selected Timeline clips, ready storyboard rows, and succeeded render outputs while keeping status text, download, and open-in-new-tab actions.
- Split timeline API type files to keep `timeline.types.ts` under the TypeScript hard file-size limit.
- Documented the new read-only API in `docs/timeline-rendering-pipeline.md`.

## Validation

- Backend focused tests: `cd ai-pic-backend && pytest tests/test_timeline_resolved_videos_api.py tests/unit/services/render/test_timeline_render_rework_assets.py -q` -> passed, 2 tests.
- Frontend focused tests: `cd ai-pic-frontend && npx tsx --test tests/timelineWorkspaceHelpers.test.ts tests/timelineWorkspaceLayout.test.tsx tests/workspaceStoryboardTabContent.test.tsx` -> passed, 27 tests.
- Frontend lint: `cd ai-pic-frontend && npm run lint` -> passed with 3 existing warnings in unrelated files.
- Frontend build: `cd ai-pic-frontend && npm run build` -> passed.
- Repo docs: `python scripts/check_repo_docs.py` -> passed.
- Repo contracts and whitespace: `python scripts/check_repo_contracts.py --mode diff <changed files>` and `git diff --check -- <changed files>` with a temporary Git index for untracked files -> passed.
- Browser evidence: Chrome DevTools connection to `127.0.0.1:9222` failed, so validation fell back to Playwright driving local Google Chrome headless.
- Browser run ID: `resolved-video-visibility-20260611T120854Z`.
- Browser artifacts: `artifacts/runs/resolved-video-visibility-20260611T120854Z/browser-evidence.json`, `timeline-video-players.png`, and `storyboard-row-video-player.png`.
- Browser assertions passed: selected Timeline clip player, succeeded render output player, and storyboard row player were visible and had controls.
- Browser network evidence: `/api/v1/timelines/66/resolved-videos` returned 200 with `ready=true`; `/api/v1/timelines/66/render-jobs` returned 200 with a succeeded output asset.
- Local browser data note: existing local timelines had no ready video or succeeded render output, so temporary dev DB rows were inserted for Timeline 66 and removed after evidence capture.
- Residual browser noise: unrelated local upload/environment image requests returned 404 or were aborted during navigation; the new Timeline video and render APIs returned 200.

## Next Steps

- None required for this implementation. Real operator pages will show inline players when clip assets, Timeline direct URLs, storyboard fallback videos, or render output assets exist.

## Linked Commits

- Not committed yet.
