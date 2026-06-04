## User Prompt

http://localhost:8089/episodes/0d2c8a2adfb9464b85116ecf8ca68c16/workspace?tab=storyboard&scriptId=128 已经生成了时间轴，但是音轨 没有播放入口，同时没有显示时间轴信息

## Goals

- Reproduce the storyboard tab state for episode `0d2c8a2adfb9464b85116ecf8ca68c16`, script `128`.
- Keep storyboard as a Timeline support view while surfacing the selected native Timeline spec.
- Add a playback entry for the Timeline source audio when the spec exposes an audio URL.

## Changes

- Added `buildStoryboardTimelineOverview()` in `WorkspaceStoryboardSupportModel.ts` to derive Timeline label, status, duration, track/clip counts, dialogue/video counts, audio version, and audio URL from native Timeline Spec v1.
- Updated storyboard summary fallback so `时间轴来源` uses the selected native Timeline ID/version when storyboard metadata is absent.
- Added a compact `当前时间轴` panel to `WorkspaceStoryboardTabContent.tsx` with Timeline details and an `<audio controls>` player for the source audio.
- Added focused regression coverage for the pure Timeline overview model and the storyboard tab audio/Timeline UI.

## Validation

1. Local checks:

- `/opt/homebrew/bin/npm run lint` -> pass with 18 pre-existing warnings in `eslint.config.mjs`, `EnvironmentReferenceImagesField.tsx`, `StoryboardEditor.js`, and `VirtualIPReferenceImagesField.tsx`.
- `/opt/homebrew/bin/npm run test` -> fail due 3 pre-existing/unrelated timeline clip storyboard tests: missing `timelineAPI.generateTimelineClipStoryboard`, changed `clip_storyboard_panel` payload expectation, and missing `timelineClipStoryboardPanelIndex`. The updated `timeline workspace helpers` and `WorkspaceStoryboardTabContent` suites both passed inside this run.
- `./node_modules/.bin/tsx --test tests/timelineWorkspaceHelpers.test.ts` -> pass, 13 tests.
- `./node_modules/.bin/tsx --test tests/workspaceStoryboardTabContent.test.tsx` -> pass, 4 tests.
- `./node_modules/.bin/eslint src/components/features/episode/WorkspaceStoryboardSupportModel.ts src/components/features/episode/WorkspaceStoryboardTabContent.tsx tests/workspaceStoryboardTabContent.test.tsx tests/timelineWorkspaceHelpers.test.ts` -> pass.
- `python3 scripts/check_repo_contracts.py --mode diff <changed files>` -> did not complete; stopped after repeated 60s no-output runs. Manual line-count check showed touched files at 365, 250, 177, 562, and 48 lines.

2. Browser or MCP validation:

- Entry URL: `http://localhost:8089/episodes/0d2c8a2adfb9464b85116ecf8ca68c16/workspace?tab=storyboard&scriptId=128`
- User path: logged in as the current AGENTS.md test account, opened the reported storyboard tab, then reloaded after the frontend change.
- Console: only React DevTools development info messages; no business errors observed.
- Network: Browser wrapper did not expose response events for this local page; DOM evidence was captured after the app loaded the Timeline state.
- Result: page showed `时间轴来源 -> Timeline 64 · v10`, `当前时间轴 -> Timeline 64 · v10`, `时长 50.0s`, `3 轨 · 49 clips`, `对白 17`, `视频 17`, `音频 v5`, and one `<audio controls>` element. The old fallback `时间轴来源 -> 当前剧本 beat` was absent.
- Evidence: `artifacts/runs/20260604T042517Z-storyboard-timeline-audio/browser-evidence.json`, `artifacts/runs/20260604T042517Z-storyboard-timeline-audio/storyboard-tab.png`.

3. Conflict signals and corrections:

- Initial shell validation attempts with login shell hung for Node commands; reran the same checks with non-login shell and absolute `/opt/homebrew/bin/npm`, which produced normal output.
- React regression test initially matched duplicate `Timeline 8 · v3` text and a split duration node; adjusted assertions to match the intended rendered UI.
- Repo contract diff script also produced no output within 60s twice and was stopped; no code conclusions were drawn from that incomplete run.

## Next Steps

- Full frontend test suite still needs the unrelated clip-storyboard expectation/API drift fixed separately.

## Linked Commits

- Not committed in this turn.
