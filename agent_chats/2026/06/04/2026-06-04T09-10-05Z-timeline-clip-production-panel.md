## User Prompt

PLEASE IMPLEMENT THIS PLAN: move Timeline clip production out of the right inspector and into a persistent main-canvas panel below the timeline, above whole-render controls.

## Goals

- Remove the Timeline workspace right-side `片段检查器`.
- Keep the left context rail and make the Timeline main canvas wider.
- Add a main-canvas `选中片段生产` panel below the Timeline.
- Keep clip-scoped storyboard and video provider generation API calls unchanged.
- Show provider generation controls only for selected `video` clips.

## Changes

- Added `EpisodeTimelineClipProductionPanel` and `EpisodeTimelineClipProductionSections` to host selected clip summary, scene environment, navigation, asset audit, and provider generation controls.
- Added a `clipProductionPanel` slot to `EpisodeTimelineMainPanel`, rendered after the Timeline canvas and before `TimelineRenderPanel`.
- Updated `EpisodeTimelineWorkspace` to stop passing an inspector to `OperatorWorkspace` and to render only the left rail plus main canvas.
- Added `showProviderControls` to `TimelineClipAssetAuditPanel` so the bottom panel can keep asset audit and manual asset recording on the left while placing provider generation on the right.
- Added `timelineWorkspaceLayout.test.tsx` to cover the removed inspector, visible bottom production panel, video clip generation controls, and hidden provider controls for non-video clips.

## Validation

- `cd ai-pic-frontend && npm run test` passed: 42 tests, 10 suites.
- `cd ai-pic-frontend && npm run lint` passed with 0 errors and 19 existing warnings.
- `cd ai-pic-frontend && npm run build` passed.
- `git diff --check` passed.
- `python3 scripts/check_repo_docs.py` passed.
- `/opt/homebrew/Cellar/python@3.12/3.12.11/Frameworks/Python.framework/Versions/3.12/bin/python3.12 scripts/check_repo_contracts.py --mode diff <changed files>` passed.
- Browser validation opened `http://localhost:8089/episodes/0d2c8a2adfb9464b85116ecf8ca68c16/workspace?tab=timeline&scriptId=128`, selected `视频 2`, confirmed `片段检查器` count was 0, `选中片段生产` count was 1, the two provider cards and buttons were visible, and the old 340px inspector grid class was absent.
- Chrome extension connection worked, but form input and localStorage write paths were blocked by the extension environment, so browser validation used Playwright with the installed Chrome executable as fallback.
- Screenshot evidence: `artifacts/runs/timeline-clip-production-2026-06-04T09-16-24-958Z/timeline-clip-production-panel.png`.
- No real AI generation buttons were clicked.

## Next Steps

- Resolve or suppress the existing frontend lint warnings separately if the team wants a warning-clean baseline.

## Linked Commits

- Pending.
