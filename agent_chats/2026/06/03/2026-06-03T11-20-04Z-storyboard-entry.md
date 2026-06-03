---
id: 2026-06-03T11-20-04Z-storyboard-entry
date: "2026-06-03T11:20:04Z"
participants: [human, codex]
models: [gpt-5]
tags: [frontend, storyboard, episode-workspace]
related_paths:
  - ai-pic-frontend/src/components/features/episode/WorkspaceActiveTabContent.tsx
  - ai-pic-frontend/src/components/features/episode/WorkspaceStoryboardActions.tsx
  - ai-pic-frontend/src/components/features/episode/WorkspaceStoryboardGridContent.tsx
  - ai-pic-frontend/src/components/features/episode/WorkspaceStoryboardTabContent.tsx
  - ai-pic-frontend/tests/workspaceStoryboardTabContent.test.tsx
summary: "Restore storyboard generation entry in the episode workspace"
---

## User Prompt

http://localhost:8089/episodes/7de415c975a94c31ac32194e11da2e34/workspace?tab=storyboard&scriptId=131 现在没有生成分镜的入口了

## Goals

- Restore a visible storyboard-generation entry on the episode workspace storyboard tab.
- Keep Timeline-native grid storyboard generation available for native Timeline specs.
- Preserve a usable fallback for scripts that still only have legacy `audio_timeline` data.

## Changes

- Added `WorkspaceStoryboardActions` to own storyboard submit actions and keep the main tab under TSX file-size limits.
- Made the storyboard tab header show `生成宫格分镜` when a native Timeline spec is present.
- Added a legacy `同步分镜占位` action when the selected script has `audio_timeline` data but no native Timeline spec.
- Passed `selectedAudioTimeline`, `selectedTimelineSpec`, and `showAlert` through the workspace active-tab boundary.
- Added a component test covering the default native Timeline entry and the legacy audio timeline fallback.
- Kept the grid storyboard panel as a display surface and moved grid submission state out of it.

## Validation

1. Local checks:

- `cd ai-pic-frontend && npx tsx --test tests/workspaceStoryboardTabContent.test.tsx` -> pass.
- `cd ai-pic-frontend && npm run test` -> pass, 33 tests.
- `cd ai-pic-frontend && npm run lint` -> pass with 18 pre-existing warnings.
- `python scripts/check_repo_docs.py` -> pass.
- `python scripts/check_repo_contracts.py --mode diff ai-pic-frontend/src/components/features/episode/WorkspaceActiveTabContent.tsx ai-pic-frontend/src/components/features/episode/WorkspaceStoryboardTabContent.tsx ai-pic-frontend/src/components/features/episode/WorkspaceStoryboardActions.tsx ai-pic-frontend/src/components/features/episode/WorkspaceStoryboardGridContent.tsx ai-pic-frontend/tests/workspaceStoryboardTabContent.test.tsx` -> pass after splitting the oversized tab file.

2. Browser validation:

- Entry URL: `http://localhost:8089/episodes/7de415c975a94c31ac32194e11da2e34/workspace?tab=storyboard&scriptId=131`.
- Engine: in-app Browser fallback. Chrome DevTools MCP could not connect because `http://127.0.0.1:9222/json/version` returned HTTP Not Found.
- User path: logged in with the repo test account, opened the target storyboard tab, and did not submit a generation task.
- Console: no warn/error findings.
- Result: `分镜辅助工作区` heading count `1`; `同步分镜占位` button count `1`; button enabled `true`.
- Artifact: `artifacts/runs/2026-06-03T11-20-04Z-storyboard-entry/browser_validation.json`.

3. Conflict signals and corrections:

- Initial assumption: the entry was only hidden behind the `宫格故事板` sub-mode.
- Contradicting evidence: the real page used legacy `audio_timeline` with no native Timeline spec, so the grid action was also disabled.
- Correction: added a legacy audio timeline sync action while keeping native Timeline grid generation separate.

## Next Steps

- None for this fix.
- A future cleanup can move remaining legacy audio timeline storyboard users onto the one-click Timeline pipeline.

## Linked Commits

- Not committed yet.
