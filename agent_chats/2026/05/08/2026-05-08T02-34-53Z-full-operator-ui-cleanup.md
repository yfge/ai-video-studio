---
id: 2026-05-08T02-34-53Z-full-operator-ui-cleanup
date: 2026-05-08T02:34:53Z
participants: [human, codex]
models: [gpt-5]
tags: [frontend, ui, operator, cleanup, admin, auth, harness]
related_paths:
  - ai-pic-frontend/src/app
  - ai-pic-frontend/src/components
  - scripts/harness
summary: "Remove full-site legacy UI remnants and align pages to the operator shell"
---

## User Prompt

PLEASE IMPLEMENT THIS PLAN: 全站 Operator UI 残留清理计划. Expand the cleanup to all app pages, including production routes, tasks, script detail, admin, login/register, and test-auth. Keep backend APIs, database, route semantics, and business flows unchanged, while aggressively deleting replaced legacy UI components and exports.

## Goals

- Make all visible routes use the IP-centered operator visual language.
- Replace old `Navigation` and `AdminLayout` with operator shells.
- Remove unreferenced legacy story, episode, layout, and image header components after verifying no imports remain.
- Keep all touched TS/TSX files within the repo file-size contract.
- Add browser harness coverage for auth, admin, and script detail pages.

## Changes

- Extended `shared/operator` with `OperatorAuthFrame` and `OperatorAdminShell`; `OperatorShell` now supports production and admin navigation modes.
- Rebuilt `/login`, `/register`, and `/test-auth` using the operator auth frame.
- Replaced admin users, stats, settings, and redirect loading UI with operator shell/panels; split oversized admin users page into focused content and row components.
- Reworked `/tasks` to use `OperatorShell`, operator panels, compact task rows, status pills, and operator controls.
- Reworked `/scripts/[id]`, script header, workflow steps, script overview, scenes, structure editor, and traffic tab into operator panels/workspaces.
- Tightened story readiness, episode overview, characters tab, script list, story generation form, character selector, and smart input suggestion surfaces.
- Removed emoji/color-heavy hook badges that were still reachable through script/storyboard surfaces.
- Deleted unused legacy `Navigation`, `AdminLayout`, old story cards/headers/detail sections, old episode header/details/audio timeline, unused image header, and the unused AI generation process component.
- Added harness scenarios for register, test-auth, admin users/stats/settings, and script detail; added `--script-id` support to `browser_flow.py`.

## Validation

- `git diff --check` passed.
- `python scripts/check_repo_docs.py` passed.
- `python scripts/check_repo_contracts.py --mode diff $(git diff --name-only)` passed.
- `cd ai-pic-frontend && npm run lint` passed with 0 errors and 19 pre-existing warnings in `eslint.config.mjs`, `StoryboardEditor.js`, and image reference fields.
- `cd ai-pic-frontend && npm run test` passed: 10 tests, 3 suites.
- `cd ai-pic-frontend && npm run build` passed after fixing two TypeScript narrowing issues in `SceneStructurePanel` and `ScriptScenesTab`.
- Residual search passed with no matches for `<Navigation`, `AdminLayout`, layout imports, `bg-gradient-to`, or explicit emoji markers in `ai-pic-frontend/src`.
- Browser evidence stored under `artifacts/runs/ui-full-operator-cleanup-20260508T023902Z/`.
- `python scripts/harness/doctor.py --run-id ui-full-operator-cleanup-20260508T023902Z --frontend-url http://localhost:8089` passed. The first default doctor attempt failed because the local stack does not expose frontend port `3000`; nginx/frontend is available on `8089`.
- Browser scenarios passed with Playwright fallback: `login_smoke`, `register_smoke`, `test_auth_smoke`, `admin_users_smoke`, `admin_stats_smoke`, `admin_settings_smoke`, `task_details_trace_smoke`, `workbench_smoke`, `virtual_ip_list_smoke`, `virtual_ip_detail_smoke`, `virtual_ip_image_generation_smoke`, `environment_asset_smoke`, `environment_detail_smoke`, `story_master_detail_smoke`, `episode_timeline_smoke`, `episode_workspace_storyboard_smoke`, `episode_script_generation_form_smoke`, and `script_detail_smoke`.
- Chrome DevTools was attempted first for each browser run and degraded to Playwright because `http://127.0.0.1:9222` timed out. Playwright console evidence includes expected dev HMR websocket 404 noise behind nginx.
- `script_detail_smoke` initially failed with default `script_id=1` because `/api/v1/scripts/1` returned 404; reran with current real script `127` and passed.
- `python scripts/harness/trace_run.py --run-id ui-full-operator-cleanup-20260508T023902Z` passed.
- `pre-commit run --all-files` was not run; this UI-only cleanup used the focused repo, frontend, and browser gates above.

## Next Steps

- Replace remaining large legacy shared modals in a focused pass if screenshots show they still dominate admin workflows.
- Continue reducing non-route hook/demo components if they become visible in product routes.

## Linked Commits

- This commit: `refactor(ui): clean up full operator surfaces`.
