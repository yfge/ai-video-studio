## User Prompt

PLEASE IMPLEMENT THIS PLAN: improve episode pages by keeping the workspace on the `Episode -> Timeline -> selected video clip -> render/export` path, removing visible scene/episode grid storyboard generation, fixing Episode character/IP binding reads, and unifying `resolved-videos` state.

## Goals

- Remove current episode-page access to whole-scene / whole-episode grid storyboard generation while preserving legacy read surfaces.
- Normalize historical Episode character `scene_appearances` payloads so role/IP binding reads do not 500.
- Use one page-level `resolved-videos` data source for header, Timeline workspace, and storyboard support view.
- Validate with targeted backend/frontend tests and real browser evidence.

## Changes

- Added response-boundary normalization for `EpisodeCharacterResponse.scene_appearances`, converting legacy scalar entries such as `[4]` into `[{"scene_number": 4}]`.
- Added API coverage for numeric and business-id Episode character list paths with legacy `scene_appearances`.
- Removed `WorkspaceStoryboardSceneGridPanel` from the current storyboard tab so the page no longer exposes `生成宫格分镜图` or `宫格图生成成片`.
- Lifted `useTimelineResolvedVideos` to the workspace page and passed `resolvedVideos`, `resolvedVideosError`, and `reloadResolvedVideos` down to header, Timeline, and storyboard support components.
- Added `useEpisodeWorkspaceUrlState` to keep the Next.js workspace page at the line-count boundary while adding page-level state wiring.

## Validation

- `cd ai-pic-backend && pytest tests/test_episode_characters_api.py -q`
  - Passed: 1 test.
- `cd ai-pic-frontend && npx tsx --test tests/timelineWorkspaceLayout.test.tsx tests/workspaceStoryboardTabContent.test.tsx tests/timelineWorkspaceHelpers.test.ts`
  - Passed: 27 tests.
- `cd ai-pic-frontend && npm run lint`
  - Passed with existing warnings only: anonymous default export in `eslint.config.mjs`, and two existing `@next/next/no-img-element` warnings.
- `cd ai-pic-frontend && npm run build`
  - Passed; Next.js production build completed for `/episodes/[id]/workspace`.
- `cd ai-pic-backend && python run_tests.py quick`
  - Blocked before test execution during dependency setup: pip cannot resolve `pydantic==2.5.0` with `langchain-core==0.2.43` on this Python 3.13 environment because `langchain-core` requires `pydantic>=2.7.4` for `python_full_version >= "3.12.4"`.
- `python scripts/check_repo_contracts.py --mode diff ...`
  - Passed.
- `git diff --check`
  - Passed.
- `cd ai-pic-frontend && npx tsc --noEmit --pretty false`
  - Not used as a gate; after this change's type errors were fixed, it still reports existing unrelated test typing errors in `tests/timelineClipGenerationTaskTracker.test.ts` and `tests/toastProvider.test.tsx`.
- Direct runtime API check:
  - `GET http://localhost:8000/api/v1/episodes/172/characters?page_size=50` returned 200 and normalized `scene_appearances` to `[{"scene_number": 4}]`.
- Browser validation:
  - Engine: Playwright fallback using system Google Chrome.
  - Evidence: `artifacts/runs/episode-page-main-path-20260611T124309Z/browser-evidence.json`.
  - Timeline URL: `http://localhost:8089/episodes/12c6eb572eda47138a5fc821c225a1af/workspace?tab=timeline&scriptId=143&clipId=video_scene_580_beat_3911_001`.
  - Storyboard URL: `http://localhost:8089/episodes/12c6eb572eda47138a5fc821c225a1af/workspace?tab=storyboard&scriptId=143`.
  - Result: no console errors, no `/characters` 500, one `/resolved-videos` request per page, Timeline main path visible, storyboard support visible, no scene-grid generation entry.

## Next Steps

- Optional cleanup: retire or hide unmounted legacy scene-grid frontend files once no other route imports them.
- Optional broader backend check before commit: `cd ai-pic-backend && python run_tests.py quick`.

## Linked Commits

- None yet.
