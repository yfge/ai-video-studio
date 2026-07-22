---
id: 2026-07-19T14-33-15Z-restore-story-novel-entry
date: "2026-07-19T14:33:15Z"
participants: [human, codex]
models: [gpt-5]
tags: [frontend, story, novel-export, regression]
related_paths:
  - ai-pic-frontend/src/components/features/stories/StoryProductionDetail.tsx
  - ai-pic-frontend/src/components/features/story-detail/StoryNovelExportPanel.tsx
  - ai-pic-frontend/src/utils/api/endpoints/story-novel.endpoints.ts
summary: "Restore the missing story-to-novel entry on story detail"
---

## User Prompt

故事导成小说的入口没有了

## Goals

- Restore a visible story-to-novel entry on the story detail page.
- Keep the existing async backend generation and download flow usable.
- Preserve concurrent story-outline work in the dirty worktree.

## Changes

- Added an Operator-style `故事导成小说` panel to the story detail page.
- Restored the focused frontend endpoint wrapper for task creation and download.
- Added a component regression test for entry visibility and async task creation.

## Validation

1. Local checks:

- `cd ai-pic-frontend && npx tsx --test tests/storyNovelExportPanel.test.tsx` -> passed, 1 test.
- `cd ai-pic-frontend && npm run lint` -> passed with 0 errors and 3 pre-existing warnings.
- `cd ai-pic-frontend && npm run test` -> repository baseline not clean: 442 passed and 9 existing Production Canvas tests failed because chat-bar fixtures omit `planningSettings` and planner auto-execution assertions do not settle.
- `cd ai-pic-frontend && npx tsc --noEmit` -> repository baseline not clean; existing Canvas and story-list test fixtures have stale required props and unrelated type errors. The new files were not named in the output.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>` -> passed; `StoryProductionDetail.tsx` remains within the 250-line limit at 249 lines.
- `git diff --check` -> passed.
- `npm run build` was not run because this change adds a colocated client component without changing routes, layouts, auth, SSR, configuration, or hydration boundaries; lint, the focused behavior test, and the real-page browser check cover the changed risk.
- `pre-commit run --all-files` and `./docker/build_prod_images.sh` were not run because no commit was requested.

2. Browser validation:

- Entry URL: `http://localhost:8090/stories/cc05f0658ea8494c80676ca074c1adaa?generate=episodes#episode-generation`.
- User path: log in -> stories -> first real story detail -> locate `故事导成小说` -> trigger `生成小说` -> observe task `#987654` and `/tasks?task_id=987654` link.
- Console: no warnings or errors.
- Network: real login, story list, and story detail requests returned 200. The novel generation POST and task polling GET were intercepted with 200 responses to prove the UI action without starting a paid AI task.
- Result: heading, target-word input, optional chapter-count input, generate action, task state, and task link were visible.
- Evidence: `artifacts/runs/story-novel-entry-20260719T143315Z/browser_flow.json` and `screenshot.png`.

3. Conflict signals and corrections:

- Initial code search showed the backend novel endpoints still existed, while the frontend section and endpoint wrapper had been removed by the Operator UI cleanup.
- Chrome DevTools connection was attempted twice and failed because `http://127.0.0.1:9222/json/version` returned HTTP Not Found.
- Browser validation explicitly fell back to Playwright with system Chrome; no Chrome DevTools verification is claimed.

## Next Steps

- None planned.

## Linked Commits

- This commit.
