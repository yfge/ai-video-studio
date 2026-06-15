## User Prompt

现在时间轴管理各种参考图选择都没了？？

## Goals

- Restore visible reference image controls in the Timeline clip production surface.
- Keep compact generation actions while avoiding hiding reference choices behind collapsed parameter menus.
- Add regression coverage for the visible reference controls.

## Changes

- Moved storyboard reference controls out of the compact parameter details in `TimelineClipStoryboardReferenceCard.tsx`.
- Moved video binding context and video reference source out of the compact parameter details in `TimelineClipVideoReworkCard.tsx`.
- Added a regression test that asserts IP image, environment image, manual reference URL, and video reference source controls are not descendants of collapsed parameter details.

## Validation

1. Local checks:

- `cd ai-pic-frontend && npx tsx --test tests/timelineClipReworkControls.test.ts` -> pass; new regression failed before implementation and passes after the fix.
- `cd ai-pic-frontend && npm run lint` -> pass with 3 existing warnings in `eslint.config.mjs`, `EnvironmentReferenceImagesField.tsx`, and `VirtualIPReferenceImagesField.tsx`.
- `cd ai-pic-frontend && npm run test` -> fails only on existing `tests/toastProvider.test.tsx` timeout after its assertion passes; all other 110 tests pass, including Timeline workspace and clip rework suites.
- `cd ai-pic-frontend && npx tsx --test tests/toastProvider.test.tsx` -> reproduces the same isolated timeout, confirming it is not caused by this Timeline change.

2. Browser or MCP validation:

- Entry URL: `http://localhost:8089/login?next=%2Fepisodes%2F340cacb9ed854bb18d50f2c69547bf03%2Fworkspace%3Ftab%3Dtimeline`
- User path: logged in with the repository test account, redirected to `/episodes/340cacb9ed854bb18d50f2c69547bf03/workspace?tab=timeline&scriptId=142&clipId=video_scene_577_beat_3886_001`, inspected the selected video clip production panel.
- Console: in-app Browser Playwright fallback recorded no warning or error logs.
- Network: curl API evidence recorded 200 responses for episode `163`, timeline `67` version `3`, resolved videos, and clip assets.
- Result: `附加参考图 URL`, `绑定角色 IP`, `选择 IP 图`, `选择环境图`, `视频生成绑定上下文`, and `视频参考来源` are present, visible, and not inside `[data-clip-parameter-details]`.
- Layout: at the default 1280px browser viewport, the compact command rail, storyboard reference controls, video reference controls, and production dock did not overflow.
- Evidence: `artifacts/runs/2026-06-14T18-26-52Z-timeline-reference-controls/browser-evidence.json`, `artifacts/runs/2026-06-14T18-26-52Z-timeline-reference-controls/api-evidence.json`, and `artifacts/runs/2026-06-14T18-26-52Z-timeline-reference-controls/layout-evidence.json`.

3. Conflict signals and corrections:

- Initial assumption: the reference controls might have been removed.
- Contradicting evidence: code search showed they still existed but had been moved under compact `...` details in the latest Timeline workspace streamline change.
- Reproduction and fix: added a failing regression for controls hidden under `[data-clip-parameter-details]`, then moved only reference-selection controls back into the always-visible production panel.
- Final verified state: targeted Timeline tests pass and browser fallback confirms visible controls in the local Timeline workspace.

## Next Steps

- Fix the unrelated `tests/toastProvider.test.tsx` open-handle timeout in a separate change.
- If committing this change, rerun the relevant checks and include this ledger entry in the same commit.

## Linked Commits

- Not committed in this turn.
