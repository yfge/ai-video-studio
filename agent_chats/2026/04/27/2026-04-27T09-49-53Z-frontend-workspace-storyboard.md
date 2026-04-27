## User Prompt

PLEASE IMPLEMENT THIS PLAN:

前端主链路收敛与 Storyboard 拆分计划。将主操作链路统一为 `Story -> Episode Workspace -> Timeline -> Storyboard support view`，下线 `/episodes/[id]/storyboard` 直达页面，把分镜编辑能力迁入 `/episodes/[id]/workspace?tab=storyboard`，更新 helper、跳转、harness/docs/contract baseline，并补充验证。

## Goals

- Remove the direct `/episodes/[id]/storyboard` frontend route without compatibility redirect.
- Route active storyboard entry points through `/episodes/[id]/workspace?tab=storyboard`.
- Add a canonical episode workspace route helper.
- Host the existing storyboard editor capability inside the episode workspace storyboard tab.
- Update harness scenarios, contract allowlists, and docs references.
- Record static, frontend, and browser validation evidence.

## Changes

- Added `episodeWorkspaceHref` and `EpisodeWorkspaceTab` in `ai-pic-frontend/src/utils/routes.ts`.
- Replaced active storyboard/timeline navigation in story detail, script detail, episode redirect, and workspace controller code with the canonical workspace helper.
- Deleted `ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx`.
- Moved the existing storyboard editor behavior into `ai-pic-frontend/src/components/features/storyboard/StoryboardEditor.js` and rendered it from `WorkspaceStoryboardTabContent`.
- Updated docs and contract audit baseline to remove the old oversized storyboard page/choke-point reference.
- Updated harness scenarios so `episode_timeline_smoke` targets workspace timeline and added `episode_workspace_storyboard_smoke`.
- Hardened harness browser evidence collection:
  - wait for login response and `auth_token` before navigating;
  - tolerate missing Playwright accessibility snapshot support;
  - avoid failing a completed CDP run because of delayed temp profile cleanup;
  - write scenario-specific browser/console/network evidence files.
- Fixed lite compose frontend env injection so `NEXT_PUBLIC_API_URL` follows the per-run nginx port.

## Validation

- `python scripts/check_repo_docs.py` passed.
- `python scripts/check_repo_contracts.py --mode diff ...` passed for the active changed files.
- `python scripts/check_repo_contracts.py --mode audit` passed.
- `cd ai-pic-frontend && npm run lint` passed with warnings only. New migrated storyboard component still has hook dependency warnings to resolve in a later fine-grained split.
- `cd ai-pic-frontend && npm run test` passed: 5 tests.
- `cd ai-pic-frontend && npm run build` passed. The route table includes `/episodes/[id]/workspace` and no `/episodes/[id]/storyboard`.
- `scripts/harness/bootstrap_worktree.sh --mode lite` passed for run `harness-20260427T093519Z`.
- `python scripts/harness/doctor.py --run-id harness-20260427T093519Z --nginx-url http://localhost:9229 --api-url http://localhost:8229 --frontend-url http://localhost:3229 --env-file docker/.env.harness.harness-20260427T093519Z` passed.
- Confirmed `http://localhost:9229/episodes/1/storyboard` returns HTTP 404.
- `python scripts/harness/browser_flow.py --scenario episode_timeline_smoke --run-id harness-20260427T093519Z --base-url http://localhost:9229 --episode-id 1` passed using Playwright fallback.
  - Evidence: `artifacts/runs/harness-20260427T093519Z/browser_flow.episode_timeline_smoke.json`
  - Screenshot: `artifacts/runs/harness-20260427T093519Z/screenshots/episode_timeline_smoke.png`
- `python scripts/harness/browser_flow.py --scenario episode_workspace_storyboard_smoke --run-id harness-20260427T093519Z --base-url http://localhost:9229 --episode-id 1` passed using Playwright fallback.
  - Evidence: `artifacts/runs/harness-20260427T093519Z/browser_flow.episode_workspace_storyboard_smoke.json`
  - Screenshot: `artifacts/runs/harness-20260427T093519Z/screenshots/episode_workspace_storyboard_smoke.png`
- Chrome DevTools validation attempted first but degraded to Playwright because the CDP endpoint timed out at `http://127.0.0.1:9222`. This fallback is recorded in both browser evidence files.

## Next Steps

- Split `StoryboardEditor.js` into smaller typed hooks/components in a follow-up pass; the current migration keeps behavior intact under workspace but still carries the old editor's internal state shape and hook dependency warnings.
- Investigate unrelated harness console/network noise observed during smoke runs: Next dev HMR 404 through nginx, empty storyboard 404 before generation, and model list 503 in mock lite mode.

## Linked Commits

- None yet.
