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
  - ai-pic-frontend/src/components/features/Timeline/Timeline.tsx
  - ai-pic-frontend/src/components/features/Timeline/TimelineOverview.tsx
  - ai-pic-frontend/src/components/features/Timeline/TimelineToolbar.tsx
  - ai-pic-frontend/src/components/features/episode/ClipProductionActionShell.tsx
  - ai-pic-frontend/src/components/features/episode/EpisodeTimelineCanvasPanel.tsx
  - ai-pic-frontend/src/components/features/episode/EpisodeTimelineClipAssetStage.tsx
  - ai-pic-frontend/src/components/features/episode/EpisodeTimelineClipProductionPanel.tsx
  - ai-pic-frontend/src/components/features/episode/EpisodeTimelineClipProductionSections.tsx
  - ai-pic-frontend/src/components/features/episode/EpisodeTimelineClipSupportPanel.tsx
  - ai-pic-frontend/src/components/features/episode/EpisodeTimelineMainPanel.tsx
  - ai-pic-frontend/src/components/features/episode/EpisodeTimelineRenderPanel.tsx
  - ai-pic-frontend/src/components/features/episode/EpisodeTimelineWorkspaceModel.ts
  - ai-pic-frontend/src/components/features/episode/TimelineClipKeyframeCard.tsx
  - ai-pic-frontend/src/components/features/episode/TimelineClipProviderReworkCards.tsx
  - ai-pic-frontend/src/components/features/episode/TimelineClipProviderReworkControls.tsx
  - ai-pic-frontend/src/components/features/episode/TimelineClipProviderReworkModel.ts
  - ai-pic-frontend/src/components/features/episode/TimelineClipSharedReferenceContext.tsx
  - ai-pic-frontend/src/components/features/episode/TimelineClipStoryboardReferenceCard.tsx
  - ai-pic-frontend/src/components/features/episode/TimelineClipVideoReworkCard.tsx
  - ai-pic-frontend/src/components/features/episode/WorkspaceStoryboardClipManagementStatus.ts
  - ai-pic-frontend/tests/timelineClipReworkControls.test.ts
  - ai-pic-frontend/tests/timelineWorkspaceHelpers.test.ts
  - ai-pic-frontend/tests/timelineWorkspaceLayout.test.tsx
summary: Restore the selected storyboard preview and redesign the Timeline workspace around the time axis and media assets.
---

## User Prompt

`http://localhost:8090/episodes/49/workspace?tab=timeline&scriptId=30&clipId=video_scene_90_beat_3991_001 没看到分镜图`

`这个页面太 TMD 丑了，简直不是给人看的`

`整体进行优化，以时间轴和资产为核心 整体重新设计`

## Goals

- Reproduce the missing storyboard image on the exact episode Timeline route.
- Verify whether the image is absent from persisted data or only missing from the selected-clip UI.
- Restore the preview without changing Timeline identity, timing, or generated media.
- Rebuild the page hierarchy around the full-episode time axis and selected-clip assets.
- Keep advanced references, bindings, asset audit, and secondary navigation available without letting them dominate the page.

## Changes

- Enriched native Timeline video items with the persisted storyboard frame that has the same stable `timeline_clip_id`, reusing the existing storyboard-frame matcher.
- Allowed the selected-clip storyboard preview to use the frame's direct `image_url`, `start_image_url`, or `end_image_url` when a clip storyboard sheet reference is absent.
- Added a focused regression test proving a v39 Timeline clip can reuse its matching persisted storyboard frame image.
- Reworked the page into three deliberate layers: full-episode Timeline, selected-clip asset workbench, and compact episode output asset.
- Added a dark selected-clip asset stage with tabs for storyboard, clip video, start frame, and end frame; the storyboard is the default visible asset when available.
- Moved storyboard preview out of the generation action card, removed the detached clip-video preview, and made asset history visible as a compact count.
- Rebuilt storyboard, keyframe, and video generation as equal production cards with visible step labels.
- Collapsed shared references, character/environment image controls, video bindings, asset audit, and secondary navigation by default.
- Simplified the Timeline frame and toolbar styling, and reduced the completed episode render player to a bounded output card.
- Updated layout and behavior tests to encode the new asset-centered information hierarchy.

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

5. Asset-centered redesign browser validation:

- Entry URL: `http://localhost:8090/episodes/49/workspace?tab=timeline&scriptId=30&clipId=video_scene_90_beat_3991_001`
- Preferred Chrome DevTools attempt failed because the local `9222` endpoint did not become available; validation explicitly used Playwright with system Chrome fallback.
- The page loaded the exact deep link and displayed the full Timeline first, followed by `选中片段资产`, asset tabs, and the three production cards.
- The storyboard asset loaded from `https://resource.lets-gpt.com/ai-generated/storyboard/image/20260715/054137/89aafbd2.png` with HTTP `200`.
- Timeline, render jobs, current-version clip assets, resolved videos, models, environments, and character requests returned `200`.
- Console contained the same unrelated missing local upload `404`; no new application error appeared.
- Draft evidence: `ai-pic-frontend/artifacts/runs/episode49-timeline-assets-redesign-20260716T2045Z/draft.png`.
- Final evidence: `ai-pic-frontend/artifacts/runs/episode49-timeline-assets-redesign-20260716T2045Z/final.png`.
- Interaction evidence: switching from the default storyboard asset to `片段视频` loaded `https://resource.lets-gpt.com/ai-generated/videos/video/20260711/201156/7daef6a9.mp4`, then switching back restored the storyboard preview.
- Interaction artifacts: `ai-pic-frontend/artifacts/runs/episode49-timeline-assets-redesign-20260716T2045Z/video-tab.png` and `interaction.json`.

6. Redesign-focused checks:

- `cd ai-pic-frontend && npx tsx --test tests/timelineWorkspaceLayout.test.tsx tests/timelineClipReworkControls.test.ts tests/timelineWorkspaceHelpers.test.ts` -> passed (`88` tests).
- `cd ai-pic-frontend && npm run lint` -> passed with zero errors and three pre-existing warnings.
- `cd ai-pic-frontend && npm run test` -> passed (`427` tests across `95` suites).
- `cd ai-pic-frontend && npm run build` -> passed, including TypeScript, static page generation, and the dynamic episode workspace route.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff <changed frontend files>` -> passed.
- `git diff --check` -> passed.
- The final combined commit gate also built the local production frontend and backend Dockerfiles successfully through BuildKit with `--pull=false`; no image was pushed.

## Next Steps

- No remaining action for this report. Commit only if requested.

## Linked Commits

- Included in this commit.
