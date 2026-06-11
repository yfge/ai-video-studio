---
id: 2026-06-11T09-34-29Z-storyboard-entry-simplification
date: "2026-06-11T09:34:29Z"
participants:
  - user
  - codex
models:
  - GPT-5 Codex
tags:
  - frontend
  - storyboard
  - timeline
related_paths:
  - ai-pic-frontend/src/app/episodes/[id]/workspace/page.tsx
  - ai-pic-frontend/src/hooks/episode/useEpisodeWorkspaceController.ts
  - ai-pic-frontend/src/hooks/episode/timelineClipUtils.ts
  - ai-pic-frontend/src/hooks/episode/workspaceTabUtils.ts
  - ai-pic-frontend/src/components/features/episode/WorkspaceStoryboardActions.tsx
  - ai-pic-frontend/src/components/features/episode/TimelineClipProviderReworkCardSections.tsx
  - ai-pic-frontend/tests/workspaceStoryboardTabContent.test.tsx
summary: Route storyboard entrypoints directly to clip-scoped Timeline production and rename the UI around "片段分镜图".
---

## User Prompt

现在分镜的入口还是太诡异了

## Goals

- Make the storyboard entry route operators directly to clip-scoped storyboard work when a native Timeline has video clips.
- Keep the legacy audio-timeline storyboard placeholder sync available only as a compatibility path.
- Align visible copy around "片段分镜" instead of mixing "分镜", "故事板参考", and "Storyboard Panel" as separate concepts.

## Changes

- Added `firstTimelineVideoClipId()` and reused it from the episode workspace and storyboard support tab.
- Changed the workflow step action so "分镜" opens `tab=timeline&clipId=<first-video-clip>` when a video clip exists.
- Changed the storyboard support tab's primary action to "进入第一个片段分镜" and kept per-clip rows as "进入片段分镜".
- Hid the legacy "同步分镜占位" action on native clip-storyboard paths unless legacy audio timeline data is present.
- Renamed the clip-generation UI from "故事板参考图" to "片段分镜图" and updated related task/status/test labels.
- Moved the page-level storyboard-entry routing into `useEpisodeWorkspaceController` and shared `firstTimelineVideoClipId()` from `hooks/episode/timelineClipUtils.ts` so the Next.js route file stays under the page hard limit.

## Validation

1. Local checks:

- `cd ai-pic-frontend && npx tsx --test tests/workspaceStoryboardTabContent.test.tsx tests/timelineWorkspaceLayout.test.tsx tests/timelineClipReworkControls.test.ts tests/timelineClipGenerationTaskTracker.test.ts` -> passed, 26 tests.
- `cd ai-pic-frontend && npm run lint` -> passed with 0 errors and 3 existing warnings in unrelated files.
- `cd ai-pic-frontend && npm run build` -> passed.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>` -> passed.
- `git diff --check -- <changed files>` -> passed.
- `cd ai-pic-frontend && npm run test` -> interrupted after the relevant storyboard/timeline suites had passed because the full run hung in `tests/toastProvider.test.tsx`; reran the focused changed suites above.

2. Browser or MCP validation:

- Chrome DevTools MCP was attempted twice and could not connect to `127.0.0.1:9222/json/version`.
- Fallback used Playwright with system Chrome against `http://localhost:8089`.
- Entry URL: `http://localhost:8089/episodes/6/workspace?tab=storyboard&scriptId=8`.
- User path: confirmed "分镜辅助工作区", "进入第一个片段分镜", and "片段分镜管理"; clicked top entry; landed on `http://localhost:8089/episodes/6/workspace?tab=timeline&scriptId=8&clipId=video_scene_001_beat_001_001`; confirmed "选中片段生产" and "生成片段分镜图".
- Network: `/api/v1/scripts/episode/6`, `/api/v1/episodes/6/timelines`, `/api/v1/timelines/66/clip-tasks`, `/api/v1/timelines/66/render-jobs`, and `/api/v1/timelines/66/clip-assets?timeline_version=3` returned 200.
- Console: four 404 errors were observed and traced to missing `/uploads/*.png` image resources; they did not block the validated entry path.
- Evidence: `artifacts/runs/storyboard-entry-20260611T094944Z/browser-evidence.json`, `artifacts/runs/storyboard-entry-20260611T094944Z/browser-network-errors.json`, `artifacts/runs/storyboard-entry-20260611T094944Z/storyboard-entry-timeline.png`.

3. Conflict signals and corrections:

- Initial focused test run failed because both the top action and per-row action were named "进入片段分镜".
- Corrected the top action to "进入第一个片段分镜" and reran the focused suite successfully.
- `check_repo_contracts` initially failed because the route file was 218 lines after adding routing logic. Moved the routing behavior into the workspace controller hook and reduced the page to 198 lines.

## Next Steps

- Consider cleaning or regenerating the four missing local upload images if the episode 6 fixture is meant to be visually complete.

## Linked Commits

- None yet.
