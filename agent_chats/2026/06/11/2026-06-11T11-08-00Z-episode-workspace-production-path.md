## User Prompt

PLEASE IMPLEMENT THIS PLAN:

把 `/episodes/[id]/workspace` 改成 Timeline-first 的生产控制台：默认进入 Timeline 工作台，顶部只保留“当前剧本 + 生产状态 + 下一步动作”，剧本/分镜/临时角色变成辅助入口。不引入新后端 API、不复活整剧 Storyboard 主入口。

## Goals

- Replace the duplicated episode workspace header flow cards, tabs, and separate script selector with a compact production path.
- Keep Timeline as the default and primary workspace.
- Preserve scriptId and clipId deep-link behavior.
- Keep Storyboard as a support view without whole-episode generation entry points.

## Changes

- Added a focused production-state helper for episode workspace step status and next-action selection.
- Reworked `EpisodeWorkspaceHeader` into a single compact production bar with current script selection, status pills, one primary CTA, and auxiliary entries for script, storyboard reference, and temporary character/IP binding.
- Removed the standalone `WorkspaceScriptSelector` and the old large `EpisodeWorkflowSteps` card.
- Renamed the Timeline panel generation controls to `Timeline 生成设置` with a `生成 Timeline` action to match the single production path.
- Strengthened frontend tests around the compact header, Timeline generation row, clip deep links, and Storyboard support-only behavior.

## Validation

1. Local checks:

- `cd ai-pic-frontend && npx tsx --test tests/timelineWorkspaceLayout.test.tsx` -> pass, 7 tests.
- `cd ai-pic-frontend && npx tsx --test tests/workspaceStoryboardTabContent.test.tsx` -> pass, 4 tests.
- `cd ai-pic-frontend && npm run lint` -> pass with 3 existing warnings: anonymous default export in `eslint.config.mjs`, `<img>` warnings in environment/IP reference image fields.
- `cd ai-pic-frontend && npm run test` -> blocked by `tests/toastProvider.test.tsx` process not exiting after its first assertion passed; command was killed after identifying the stuck test process.
- `cd ai-pic-frontend && npx tsx --test tests/toastProvider.test.tsx` -> first assertion passed, but the single-file process also did not exit and was killed; treated as existing test harness blocker outside this workspace UI change.
- `cd ai-pic-frontend && npx tsx --test $(find tests -type f \\( -name '*.test.tsx' -o -name '*.test.ts' -o -name '*.test.js' \\) | grep -v '^tests/toastProvider.test.tsx$')` -> pass, 68 tests.
- `cd ai-pic-frontend && npm run build` -> pass.
- `python scripts/check_repo_docs.py` -> pass.
- `python scripts/check_repo_contracts.py --mode diff <changed files>` -> pass.
- `git diff --check` -> pass.
- `pre-commit run --files <changed frontend files and ledger>` -> pass after prettier reformatted `EpisodeWorkspaceHeader.tsx` and `EpisodeTimelineMainPanel.tsx`.
- `cd ai-pic-frontend && npx tsx --test tests/timelineWorkspaceLayout.test.tsx tests/workspaceStoryboardTabContent.test.tsx` -> pass after pre-commit formatting, 11 tests.
- `pre-commit run --all-files` and `./docker/build_prod_images.sh` were not run for this commit; validation was scoped to the touched frontend files and the known `tests/toastProvider.test.tsx` exit blocker.

2. Browser or MCP validation:

- Chrome DevTools MCP was unavailable: `127.0.0.1:9222/json/version` returned HTTP Not Found.
- Playwright bundled Chromium was unavailable because the local Playwright browser binary was not installed.
- Fallback used Playwright with system Chrome against local Next dev server `http://localhost:3000` and backend `http://localhost:8000`.
- Entry URL: `http://localhost:3000/episodes/4/workspace?tab=timeline`.
- Evidence: `artifacts/runs/episode-workspace-production-path-20260611T111623Z/browser-evidence.json` and `episode-workspace-production-path.png`.
- Result: page rendered `生产主线`, one `当前剧本` selector, auxiliary buttons `剧本设置` / `分镜参考` / `临时角色/IP 绑定`; legacy `步骤 1` and `剧集概要` tab button counts were 0; console and failed network request lists were empty; decisive episode/script catalog API responses returned 200.

3. Conflict signals and corrections:

- `npm run test -- tests/timelineWorkspaceLayout.test.tsx` expanded through the package script into the full test file list and did not exit promptly after the expected red failures. The test process tree was killed, then the narrow `npx tsx --test ...` command was used for focused red/green validation.
- Standard `npm run test` also blocked on the pre-existing `tests/toastProvider.test.tsx` exit issue, so coverage was recovered by running the changed tests directly plus the full frontend suite excluding that stuck file.

## Next Steps

- Decide separately whether to repair the pre-existing `tests/toastProvider.test.tsx` exit issue so the standard `npm run test` command can complete without manual process cleanup.

## Linked Commits

- Not committed.
