## User Prompt

- "需要可以在生成宫格图时选择模型！"
- Follow-up context: task `Timeline clip storyboard - video_scene_91_beat_4003_013` was suspected to have no reference images or model selection.

## Goals

- Add model selection to Timeline clip storyboard / storyboard grid generation.
- Keep existing backend request shape and only populate the existing `model` field when the operator selects a model.
- Preserve existing reference image payload fields: `reference_images`, `character_reference_images`, and `environment_reference_images`.
- Validate the request body from the real episode 49 Timeline UI.

## Changes

- Added a `分镜生图模型` select to the clip storyboard parameter popover, populated from available image models.
- Added `storyboardModel` state to clip production controls and threaded image model options from `EpisodeTimelineWorkspace` through the production panel.
- Updated `buildTimelineClipStoryboardGeneratePayload` and generation actions so selected image model is submitted as `model`.
- Added focused test coverage for submitting `model: "volcengine:doubao-seedream-4-5-251128"` with `生成片段分镜图`.
- Confirmed task `6066` / `video_scene_91_beat_4003_013` had reference images in persisted metadata; the missing operator control was the image model selector.

## Validation

- Red check: `cd ai-pic-frontend && npx tsx --test tests/timelineClipReworkControls.test.ts`
  - Failed before implementation because `分镜生图模型` did not exist.
- Green focused tests: `cd ai-pic-frontend && npx tsx --test tests/timelineClipReworkControls.test.ts tests/timelineWorkspaceLayout.test.tsx`
  - Passed: 64 tests, 0 failed.
- Lint: `cd ai-pic-frontend && npm run lint`
  - Passed with 0 errors and 3 existing warnings in `eslint.config.mjs`, `EnvironmentReferenceImagesField.tsx`, and `VirtualIPReferenceImagesField.tsx`.
- Docs: `python scripts/check_repo_docs.py`
  - Passed.
- Scoped contracts for this storyboard model-selection change:
  - `python scripts/check_repo_contracts.py --mode diff ai-pic-frontend/src/components/features/episode/EpisodeTimelineClipProductionPanel.tsx ai-pic-frontend/src/components/features/episode/EpisodeTimelineWorkspace.tsx ai-pic-frontend/src/components/features/episode/EpisodeTimelineWorkspacePanels.tsx ai-pic-frontend/src/components/features/episode/TimelineClipProviderGenerationPayloads.ts ai-pic-frontend/src/components/features/episode/TimelineClipProviderReworkCards.tsx ai-pic-frontend/src/components/features/episode/TimelineClipProviderReworkControls.tsx ai-pic-frontend/src/components/features/episode/TimelineClipProviderReworkControlsTypes.ts ai-pic-frontend/src/components/features/episode/TimelineClipStoryboardReferenceCard.tsx ai-pic-frontend/src/components/features/episode/useTimelineClipProviderGenerationActions.ts ai-pic-frontend/tests/timelineClipReworkControls.test.ts`
  - Passed.
- Full dirty-tree contracts:
  - `python scripts/check_repo_contracts.py --mode diff $(git diff --name-only --diff-filter=ACM) $(git ls-files --others --exclude-standard)`
  - Failed on existing dirty/untracked `ai-pic-frontend/src/components/features/canvas/ProductionCanvasBoard.tsx` file-size limit, currently reported as `line_count=395`.
- Whitespace: `git diff --check`
  - Passed.
- Browser validation:
  - Chrome DevTools was attempted twice and failed with `Could not connect to Chrome: http://127.0.0.1:9222/json/version HTTP Not Found`.
  - Fallback used Playwright with local Chrome.
  - Because the running frontend server at `localhost:3100` had no `NEXT_PUBLIC_API_URL` proxy and returned Next 404 for `/api/v1/auth/login`, Playwright proxied `/api/v1/**` to backend `localhost:8000`.
  - Evidence: `artifacts/runs/20260618T091805Z-storyboard-model-select-catch-all/storyboard-model-request.json`.
  - Captured POST: `http://localhost:8000/api/v1/timelines/69/clips/video_scene_90_beat_3991_001/storyboard/generate`.
  - Captured body included `model: "volcengine:doubao-seedream-4-5-251128"`, `generation_profile: "clip_storyboard"`, `character_reference_images`, and `environment_reference_images`.
  - The episode 49 page fallback selected the first video clip (`video_scene_90_beat_3991_001`) despite the attempted deep link to `video_scene_91_beat_4003_013`; backend timeline 69 data does contain `video_scene_91_beat_4003_013`.

## Next Steps

- If exact deep-link selection for `video_scene_91_beat_4003_013` is required, investigate why the Timeline workspace falls back to the first video clip even though timeline 69 contains the requested clip.
- Resolve the unrelated dirty-tree contracts blocker in `ProductionCanvasBoard.tsx` before claiming full-repository contracts pass.

## Linked Commits

- None yet.
