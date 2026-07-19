---
id: 2026-07-18T01-59-15Z-timeline-video-deep-link-playback
date: "2026-07-18T01:59:15Z"
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - timeline
  - video
  - deep-link
  - playback
related_paths:
  - ai-pic-frontend/src/hooks/useEpisodeMetadata.ts
  - ai-pic-frontend/tests/timelineMetadataLoading.test.tsx
summary: Preserve a requested Timeline clip deep link until the matching Timeline metadata has resolved.
---

## User Prompt

`http://localhost:8090/episodes/a48f8d1010044807baf22e113e1f89c1/workspace?tab=timeline&scriptId=146&clipId=video_scene_591_beat_4360_009` 生成的视频无法播放

## Goals

- Reproduce the reported generated-video playback failure on the exact clip deep link.
- Keep the requested clip selected while Timeline metadata loads.
- Prove the resolved generated video can enter an actual playing state.

## Changes

- Made Timeline metadata loading synchronous with the requested episode/script key, instead of waiting for an effect to flip the loading flag after the first render.
- Prevented the Timeline workspace from briefly mounting fallback tracks and normalizing a valid deep link to the first clip before the current Timeline response arrives.
- Added focused frontend coverage for the first-render loading contract.

## Validation

1. Persisted Timeline and media checks:

- Read-only database inspection found Timeline `76` v17 for script `146`; clip `video_scene_591_beat_4360_009` has generated video media asset `594` from `provider_rework`.
- The resolved-video service returns the clip as `ready` through `timeline_clip_asset:provider_rework` even though the generated-video link was created at Timeline v16 and the current Timeline is v17.
- The MP4 URL returned `200 video/mp4`, advertised byte ranges, returned `206` for a range request, and probed as H.264 `720x1280` plus AAC with duration `5.541667s`.

2. Frontend checks:

- `cd ai-pic-frontend && npx tsx --test tests/timelineMetadataLoading.test.tsx tests/timelineWorkspaceLayout.test.tsx` -> passed, 42 tests.
- `cd ai-pic-frontend && npm run lint` -> passed with 3 existing warnings outside the changed files.
- `cd ai-pic-frontend && npm run test` -> 439 passed, 9 failed. All failures are in the pre-existing dirty Canvas work: five `ProductionCanvasChatBar` tests read missing planning/context fields and four `ProductionCanvasPlanner` tests miss expected execution calls. Timeline metadata and workspace suites passed.
- `cd ai-pic-frontend && npm run build` -> first sandboxed run failed only because Google Fonts was unreachable; the required escalated rerun passed and generated all routes.

3. Repository checks:

- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-frontend/src/hooks/useEpisodeMetadata.ts ai-pic-frontend/tests/timelineMetadataLoading.test.tsx agent_chats/2026/07/18/2026-07-18T01-59-15Z-timeline-video-deep-link-playback.md` -> passed.
- `git diff --check -- <changed files>` -> passed.
- No backend source changed, so no backend pytest gate was required.

4. Browser validation:

- Chrome DevTools could not connect to `127.0.0.1:9222` and returned HTTP Not Found on both attempts, so validation explicitly fell back to Playwright driving local Google Chrome.
- Before the fix, the exact entry URL normalized first to no `clipId` and then to `video_scene_591_beat_4352_001`, proving the generated-video clip was not actually selected.
- After the fix, a fresh authenticated context kept the exact requested URL and selected `video-video_scene_591_beat_4360_009` (`视频 3`) without a manual Timeline click.
- Network: `GET /api/v1/timelines/76/resolved-videos` returned `200`; the selected MP4 request returned `206`.
- Media element: `readyState=4`, `networkState=1`, `error=null`, `paused=false`, and `currentTime=1.360704` after starting playback; duration was `5.541667s`.
- Console: no media errors. One unrelated existing `/uploads` image request returned 404.
- Evidence: `artifacts/runs/timeline-video-playback-20260718T0156Z/browser-evidence.json` and `screenshots/after.png`.

5. Commit-time revalidation on 2026-07-19:

- `cd ai-pic-frontend && npx tsx --test tests/timelineMetadataLoading.test.tsx tests/timelineWorkspaceLayout.test.tsx` -> passed, 42 tests. The first sandboxed attempt could not create the `tsx` IPC socket (`EPERM`); the approved unsandboxed rerun passed.
- `cd ai-pic-frontend && npm run lint` -> passed with the same 3 existing warnings outside the changed files.
- `cd ai-pic-frontend && npm run test` -> 439 passed, 9 failed with the same unrelated Production Canvas failures recorded above.
- `python scripts/check_repo_docs.py`, the changed-file repository contract check, and `git diff --check` -> passed.
- `pre-commit run --all-files` -> the existing repository baseline was not clean: formatters touched 226 historical tracked files, Ruff reported pre-existing backend errors, and the backend quick gate failed only `tests/unit/test_story_parser.py::test_extract_json_block_reexported_from_story_parser`. All formatter changes were reverted; `pre-commit run --files <the three commit paths>` then passed every applicable hook.
- `./docker/build_prod_images.sh` -> passed and pushed both `linux/amd64` and `linux/arm64` backend/frontend images with tag `63cf52ef`. The frontend install reported 2 existing audit findings (1 moderate, 1 high).
- The browser flow was not repeated because the committed frontend source and focused test were unchanged from the persisted browser evidence above.

## Next Steps

- The reported clip playback path is fixed. The unrelated dirty Canvas test failures remain with the existing Canvas work and were not modified here.
- Track the existing frontend dependency audit findings separately from this Timeline fix.

## Linked Commits

- This commit (`fix: preserve Timeline deep-link playback`).
