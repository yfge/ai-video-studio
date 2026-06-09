## User Prompt

`http://localhost:8089/episodes/ecd5d5d0b87a485ebfbc9275f1ae6ff3/workspace?tab=timeline&scriptId=125 仍然没有生成分镜 故事板 关键帧 视频的入口`

Follow-up: `commit`

## Goals

- Restore a visible Timeline-first production entry for the selected clip on the workspace Timeline tab.
- Keep storyboard and video generation clip-scoped, not whole-Timeline scoped.
- Make deep links land on a video clip when Timeline data contains video clips, so the storyboard-reference and video-generation actions are visible immediately.
- Leave unrelated backend Timeline import repair and other dirty worktree changes out of this commit.

## Changes

- Moved selected-clip production from the old right inspector into a persistent main-canvas panel below the Timeline and above whole-render controls.
- Split provider generation controls into two visible cards: `故事板参考` and `片段视频`.
- Kept storyboard reference generation on `POST /api/v1/timelines/{timeline_id}/clips/{clip_id}/storyboard/generate`.
- Kept video generation/rework on `POST /api/v1/timelines/{timeline_id}/clips/{clip_id}/rework/video`.
- Suppressed duplicate provider controls inside the asset audit panel when the new production panel owns them.
- Changed the Timeline workspace default selection to prefer the first `video` clip before falling back to the first available clip. This fixes deep links where `dialogue` tracks appear before `video` tracks and hid the storyboard/video actions.
- Added regression coverage for the two-step controls, clip-scoped request payloads, removed right inspector, main-canvas production panel, non-video hidden controls, and video-first deep-link selection.

## Validation

- `cd ai-pic-frontend && npm exec tsx --test tests/timelineWorkspaceLayout.test.tsx` -> pass, 3 tests.
- `cd ai-pic-frontend && npm run lint` -> pass, 0 errors; existing warnings remained.
- `cd ai-pic-frontend && npm run test` -> pass, 41 tests.
- `cd ai-pic-frontend && npm run build` -> pass.
- Browser validation note: Chrome DevTools MCP could not connect to local Chrome remote debugging (`http://127.0.0.1:9222/json/version` returned HTTP Not Found). Playwright fallback with the bundled browser was blocked by a missing browser binary, and Playwright fallback with system Chrome opened `localhost:8089` but stayed unauthenticated with 401 episode/script requests. No Chrome verification is claimed for this run.

## Next Steps

- Reload the reported Timeline workspace after the commit is applied; a Timeline with video clips should now select the first video clip and show `生成故事板参考图` plus `生成/重做此片段视频`.
- Re-run browser validation after the local auth/session issue is resolved.

## Linked Commits

- This commit: `fix(frontend): surface timeline clip production entry`
