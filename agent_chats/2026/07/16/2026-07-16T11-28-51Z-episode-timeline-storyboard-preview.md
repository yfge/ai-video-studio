---
id: 2026-07-16T11-28-51Z-episode-timeline-storyboard-preview
date: "2026-07-16T11:28:51Z"
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - frontend
  - episode-workspace
  - timeline
  - storyboard
  - browser-validation
related_paths:
  - ai-pic-frontend/src/components/features/episode/EpisodeTimelineWorkspaceModel.ts
  - ai-pic-frontend/src/components/features/episode/TimelineClipProviderReworkModel.ts
  - ai-pic-frontend/src/components/features/episode/WorkspaceStoryboardClipManagementStatus.ts
  - ai-pic-frontend/tests/timelineWorkspaceHelpers.test.ts
summary: Restore the selected Timeline clip storyboard preview from its matching persisted storyboard frame.
---

## User Prompt

`http://localhost:8090/episodes/49/workspace?tab=timeline&scriptId=30&clipId=video_scene_90_beat_3991_001 没看到分镜图`

## Goals

- Reproduce the missing storyboard image on the exact episode Timeline route.
- Verify whether the image is absent from persisted data or only missing from the selected-clip UI.
- Restore the preview without changing Timeline identity, timing, or generated media.

## Changes

- Enriched native Timeline video items with the persisted storyboard frame that has the same stable `timeline_clip_id`, reusing the existing storyboard-frame matcher.
- Allowed the selected-clip storyboard preview to use the frame's direct `image_url`, `start_image_url`, or `end_image_url` when a clip storyboard sheet reference is absent.
- Added a focused regression test proving a v39 Timeline clip can reuse its matching persisted storyboard frame image.

## Validation

1. Persisted data and API diagnosis:

- Timeline `69` is currently version `39`.
- `GET /api/v1/timelines/69/clip-assets?timeline_version=39&clip_id=video_scene_90_beat_3991_001` returned only `generated_video` and `render_output`.
- The all-version clip lineage still contains `clip_storyboard_sheet` asset `267` and `storyboard_image` assets `444` and `482`.
- `GET /api/v1/scripts/30/storyboard` returned the matching frame with `timeline_clip_id=video_scene_90_beat_3991_001` and `image_url=https://resource.lets-gpt.com/ai-generated/storyboard/image/20260715/054137/89aafbd2.png`.

2. Browser reproduction:

- Entry URL: `http://localhost:8090/episodes/49/workspace?tab=timeline&scriptId=30&clipId=video_scene_90_beat_3991_001`
- Engine: Playwright with system Chrome fallback because the browser plugin control interface was unavailable in this session.
- User path: log in, open the exact Timeline deep link, inspect the selected video clip production rail.
- Console: one unrelated `404` resource error.
- Network: Timeline, render-job, current-version clip-assets, and resolved-video requests returned `200`.
- Result before the fix: the page showed `先生成片段分镜图`, disabled the storyboard video reference option, and rendered zero `片段分镜图预览` images.
- Evidence: `ai-pic-frontend/artifacts/runs/episode49-storyboard-missing-20260716T1930Z/before.png` and `before.json`.

3. Local checks:

- `cd ai-pic-frontend && npx tsx --test tests/timelineWorkspaceHelpers.test.ts` -> failed before the fix because the matched frame image was not present on the selected Timeline item.
- The same focused test -> passed after the fix (`20` tests passed).
- `cd ai-pic-frontend && npm run lint` -> passed with zero errors and three pre-existing warnings.
- `cd ai-pic-frontend && npm run test` -> passed (`423` tests across `94` suites).
- `cd ai-pic-frontend && npx tsx --test tests/timelineWorkspaceHelpers.test.ts tests/timelineClipReworkControls.test.ts` -> passed (`48` tests).
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>` -> initially rejected `EpisodeTimelineWorkspaceModel.ts` at `268` lines; the duplicated lookup was replaced with the existing `matchingStoryboardFrame` helper and the final `247`-line file passed the contract.
- `git diff --check` -> passed.

4. Browser validation after the fix:

- Entry URL and engine were unchanged from the reproduction run.
- Console: the same unrelated missing local upload returned `404`; no new application error appeared.
- Network: Timeline, render-job, current-version clip-assets, and resolved-video requests returned `200`.
- Result: the chain changed from `先生成片段分镜图` to `已生成`; the clip storyboard reference option became available; one visible `片段分镜图预览` rendered.
- Image source: `https://resource.lets-gpt.com/ai-generated/storyboard/image/20260715/054137/89aafbd2.png`.
- Loaded image size: `941x1672`.
- Evidence: `ai-pic-frontend/artifacts/runs/episode49-storyboard-missing-20260716T1930Z/after.png` and `after.json`.
- `npm run build` was omitted because this change does not touch routes, layouts, auth, config, SSR, or hydration-sensitive boundaries; lint, full behavior tests, contracts, and the real browser path cover the changed surface.
- The final combined commit gate also built the local production frontend and backend Dockerfiles successfully through BuildKit with `--pull=false`; no image was pushed.

## Next Steps

- No remaining action for this report. Commit only if requested.

## Linked Commits

- Included in this commit.
