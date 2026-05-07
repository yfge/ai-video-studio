---
id: 2026-05-06T14-29-41Z-core-ui-prototype-implementation
date: 2026-05-06T14:29:41Z
participants: [human, codex]
models: [gpt-5]
tags: [frontend, backend, ui, workbench, timeline]
related_paths:
  - ai-pic-backend/app/api/v1/endpoints/workbench.py
  - ai-pic-backend/app/repositories/workbench_repository.py
  - ai-pic-backend/app/services/workbench_service.py
  - ai-pic-backend/app/schemas/workbench.py
  - ai-pic-backend/app/services/ai/scripts.py
  - ai-pic-backend/app/services/ai/scripts_ai_manager.py
  - ai-pic-backend/app/services/ai/scripts_ai_manager_payloads.py
  - ai-pic-backend/app/services/episode_agent_episode_utils.py
  - ai-pic-frontend/src/app/page.tsx
  - ai-pic-frontend/src/app/environments/page.tsx
  - ai-pic-frontend/src/app/environments/[id]/page.tsx
  - ai-pic-frontend/src/app/virtual-ip/page.tsx
  - ai-pic-frontend/src/app/virtual-ip/[id]/page.tsx
  - ai-pic-frontend/src/app/virtual-ip/[id]/VirtualIPDetailPageParts.tsx
  - ai-pic-frontend/src/app/stories/page.tsx
  - ai-pic-frontend/src/app/episodes/[id]/workspace/page.tsx
  - ai-pic-frontend/src/components/shared/operator/OperatorPrimitives.tsx
  - ai-pic-frontend/src/components/shared/operator/OperatorShell.tsx
  - ai-pic-frontend/src/components/shared/operator/StatusPill.tsx
  - ai-pic-frontend/src/components/shared/operator/ProgressBar.tsx
  - ai-pic-frontend/src/components/features/Timeline/Timeline.tsx
  - ai-pic-frontend/src/components/features/episode/EpisodeTimelineWorkspace.tsx
  - ai-pic-frontend/src/components/features/episode/EpisodeWorkflowSteps.tsx
  - ai-pic-frontend/src/components/features/episode/EpisodeWorkspaceHeader.tsx
  - ai-pic-frontend/src/components/features/episode/WorkspaceStoryboardTabContent.tsx
  - ai-pic-frontend/src/components/features/episode/WorkspaceTimelineTabContent.tsx
  - ai-pic-frontend/src/components/features/environments/EnvironmentList.tsx
  - ai-pic-frontend/src/components/features/environments/EnvironmentCreateOverlay.tsx
  - ai-pic-frontend/src/components/features/environments/EnvironmentDetailState.ts
  - ai-pic-frontend/src/components/features/environments/EnvironmentDetailView.tsx
  - ai-pic-frontend/src/components/features/environments/EnvironmentDetailViewParts.tsx
  - ai-pic-frontend/src/components/features/environments/EnvironmentGenerationFields.tsx
  - ai-pic-frontend/src/components/features/environments/EnvironmentHeader.tsx
  - ai-pic-frontend/src/components/features/environments/EnvironmentImagesPanel.tsx
  - ai-pic-frontend/src/components/features/environments/EnvironmentSidePanel.tsx
  - ai-pic-frontend/src/components/features/stories/StoryProductionBoard.tsx
  - ai-pic-frontend/src/components/features/stories/StoryProductionDetail.tsx
  - ai-pic-frontend/src/components/features/virtual-ip/VirtualIPListSection.tsx
  - ai-pic-frontend/src/components/features/virtual-ip/VirtualIPCreateModal.tsx
  - ai-pic-frontend/src/components/features/virtual-ip/VirtualIPCreateModalParts.tsx
  - ai-pic-frontend/src/components/features/virtual-ip-detail/VirtualIPAdditionalInfoSection.tsx
  - ai-pic-frontend/src/components/features/virtual-ip-detail/VirtualIPInfoSection.tsx
  - ai-pic-frontend/src/components/features/virtual-ip-detail/VoiceSettingsPanel.tsx
  - ai-pic-frontend/src/components/features/virtual-ip-images/CategoryFilter.tsx
  - ai-pic-frontend/src/components/features/virtual-ip-images/ImageGenerationForm.tsx
  - ai-pic-frontend/src/components/features/virtual-ip-images/ImageGenerationFormParts.tsx
  - ai-pic-frontend/src/components/features/virtual-ip-images/ImageGrid.tsx
  - ai-pic-frontend/src/components/features/virtual-ip-images/ImageUploadForm.tsx
  - ai-pic-frontend/src/components/features/virtual-ip-images/VirtualIPImageManager.tsx
  - ai-pic-frontend/src/components/features/workbench/WorkbenchDashboard.tsx
  - scripts/harness/browser_flow.py
  - scripts/harness/scenarios.py
summary: "Implement Timeline-first workbench, story production view, and workbench summary API from image prototypes"
---

## User Prompt

PLEASE IMPLEMENT THIS PLAN: 核心原型落地 V1. Implement the workbench summary API, authenticated operator workbench, story master-detail production view, Timeline-first episode workspace, Storyboard auxiliary wrapper, tests, harness coverage, and ledger.

Follow-up prompts requested backend validation cleanup, V2 global operator UI alignment, and then corrected the product direction: IP/environment assets have not fully migrated yet, and the project must be IP-centered rather than story-centered.

## Goals

- Add `/api/v1/workbench/summary` with user-scoped metrics, recent episodes, and task queue aggregation.
- Replace the marketing-style home page with an authenticated operator production workbench.
- Convert `/stories` into a story list + production detail view with readiness/generation controls.
- Make episode workspace links default to `tab=timeline` and make the Timeline tab the primary three-column workspace.
- Keep Storyboard as an auxiliary support surface and avoid rewriting the legacy editor.
- Add focused backend/frontend tests and browser evidence for `/`, `/stories`, timeline, and storyboard flows.

## Changes

- Added `WorkbenchSummary` schemas, repository, service, and endpoint; registered `/api/v1/workbench/summary`.
- Added backend integration tests for user scoping, metrics, episode stage derivation, and task progress aggregation.
- Added `workbenchAPI.getSummary()` plus frontend workbench types and a `useWorkbenchSummary` hook.
- Added operator shell primitives: side navigation, top bar, status pill, progress bar, compact panel/table styling.
- Replaced `/` with a production workbench showing metrics, recent episodes, task queue, failed-task retry links, and audit checks.
- Replaced `/stories` with a URL-query-selected story master-detail view; kept `/stories/[id]` accessible using the same detail component.
- Added display normalization for legacy fenced JSON story synopsis data so the new UI shows concise operator text.
- Changed `episodeWorkspaceHref()` and episode redirect defaults to `tab=timeline`; updated timeline button copy.
- Added a selectable three-column `EpisodeTimelineWorkspace` with context, multi-track Timeline, selected item inspector, and generation controls.
- Wrapped the legacy Storyboard editor in a Timeline-first auxiliary surface with a return-to-timeline entry and context strip.
- Added browser harness scenarios for `workbench_smoke` and `story_master_detail_smoke`; reused existing timeline/storyboard scenarios.
- Closed backend baseline failures by using non-streaming structured JSON script calls, restoring the direct script mixin fallback default to structured screenplay output, and preserving repaired episode summaries while filling missing scenes from outline stubs.
- Aligned the operator UI V2 visual system across workbench, story production, episode workspace shell, Timeline canvas, and Storyboard support wrapper using shared panel/header/button/table/state primitives.
- Removed prominent gradient, heavy-shadow, oversized-radius, and purple/indigo action styling from the main operator path while preserving API shape and generation behavior.
- Constrained the Storyboard support view with a stable outer workspace and scroll surface; the legacy editor internals remain unchanged.
- Re-centered the operator shell around IP projects: `/virtual-ip` is now the primary nav item, story production is downstream, and environment assets are labeled as a migration surface.
- Updated workbench copy and entry actions to state that IP/environment assets are still migrating while current production continues through existing story/episode links.
- Updated story production and episode workspace copy to treat linked story characters as IP associations, including a visible "IP 关联待迁移" fallback when the story has no migrated IP links.
- Wrapped `/virtual-ip` and `/environments` in the operator shell, added migration-state notices, and restyled the IP/environment list components to remove the old gradient CTA, heavy shadows, and thick card borders.
- Added browser harness scenarios for `virtual_ip_list_smoke` and `environment_migration_smoke` so the new IP-centered and migration-aware entrypoints are covered directly.
- Generated and self-checked the 6 IP/environment reference PNGs:
  - `artifacts/ui-prototypes/2026-05-07-ip-environment-flow/01-ip-project-list.png`
  - `artifacts/ui-prototypes/2026-05-07-ip-environment-flow/02-ip-project-detail.png`
  - `artifacts/ui-prototypes/2026-05-07-ip-environment-flow/03-ip-image-manager.png`
  - `artifacts/ui-prototypes/2026-05-07-ip-environment-flow/04-ip-create-modal.png`
  - `artifacts/ui-prototypes/2026-05-07-ip-environment-flow/05-environment-list-create.png`
  - `artifacts/ui-prototypes/2026-05-07-ip-environment-flow/06-environment-detail-generation.png`
- Brought `/virtual-ip/[id]` into the operator shell and split repeated page chrome into `VirtualIPDetailPageParts.tsx` to satisfy the repo file-size contract.
- Restyled the IP detail, background story, readiness, task/action inspector, and embedded image manager with compact operator panels and neutral buttons.
- Split `VirtualIPCreateModal.tsx` and `ImageGenerationForm.tsx` into small parts, then aligned the IP creation modal, tag field, voice settings, upload form, category filter, and image grid with the same operator primitives.
- Brought `/environments/[id]` into the operator shell and split detail state/layout into `EnvironmentDetailState.ts`, `EnvironmentDetailViewParts.tsx`, and the slim `EnvironmentDetailView.tsx`.
- Restyled the environment creation overlay, environment detail header, image pool, upload/generation side panel, and generation fields while preserving existing environment APIs and image generation flows.
- Added browser harness coverage for `virtual_ip_detail_smoke` and `environment_detail_smoke`; `browser_flow.py` now accepts `--environment-id` and injects it into scenario URL formatting.

## Validation

- `python scripts/check_repo_docs.py` passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>` passed.
- `cd ai-pic-backend && pytest tests/unit/services/ai/test_scripts_ai_manager.py::test_call_ai_manager_script_passes_max_tokens_and_repairs_json tests/unit/services/ai/test_scripts_generation_mixin.py::test_generate_script_times_out_and_falls_back_to_direct tests/unit/test_episode_step_outline_light.py::test_outline_missing_logline_triggers_repair -q` passed: `3 passed`.
- `cd ai-pic-backend && pytest tests/integration/test_workbench_summary_api.py -q` passed: `2 passed`.
- Real local API probe against Docker/MySQL: authenticated `GET /api/v1/workbench/summary` returned `200` after replacing MySQL-incompatible `NULLS LAST` ordering with `coalesce(updated_at, created_at)`.
- `cd ai-pic-backend && pytest` passed: `1946 passed, 87 skipped, 1419 warnings`.
- `cd ai-pic-frontend && npm run lint` passed with `0 errors, 19 warnings`; warnings are existing StoryboardEditor hook-dependency warnings, existing `<img>` warnings, and eslint config default-export warning.
- `cd ai-pic-frontend && npm run test` passed: `7 passed`.
- `cd ai-pic-frontend && npm run build` passed.
- V2 rerun: `cd ai-pic-frontend && npm run lint` passed with `0 errors, 19 warnings`; warnings match existing StoryboardEditor hook-dependency warnings, existing `<img>` warnings, and eslint config default-export warning.
- V2 rerun: `cd ai-pic-frontend && npm run test` passed: `7 passed`.
- V2 rerun: `cd ai-pic-frontend && npm run build` passed.
- V2 rerun: `python scripts/check_repo_docs.py` passed.
- V2 rerun: `python scripts/check_repo_contracts.py --mode diff <changed files>` passed.
- `python scripts/harness/doctor.py --run-id ui-core-v1-20260506T141509Z --nginx-url http://localhost:8089 --api-url http://localhost:8000 --frontend-url http://localhost:8089 --env-file docker/.env.lite` passed.
- Browser evidence stored under `artifacts/runs/ui-core-v1-20260506T141509Z/`.
- Browser scenarios passed with Playwright fallback after Chrome DevTools transport timed out at `http://127.0.0.1:9222`:
  - `workbench_smoke`
  - `story_master_detail_smoke`
  - `episode_timeline_smoke`
  - `episode_workspace_storyboard_smoke`
- `python scripts/harness/trace_run.py --run-id ui-core-v1-20260506T141509Z` passed and wrote `artifacts/runs/ui-core-v1-20260506T141509Z/trace-run.json`.
- V2 browser doctor passed: `python scripts/harness/doctor.py --run-id ui-global-align-20260507T054841Z --nginx-url http://localhost:8089 --api-url http://localhost:8000 --frontend-url http://localhost:8089 --env-file docker/.env.lite`.
- V2 browser evidence stored under `artifacts/runs/ui-global-align-20260507T054841Z/`.
- V2 browser scenarios passed with Playwright fallback after Chrome DevTools timed out at `http://127.0.0.1:9222`:
  - `workbench_smoke`
  - `story_master_detail_smoke`
  - `episode_timeline_smoke`
  - `episode_workspace_storyboard_smoke`
- V2 trace passed: `python scripts/harness/trace_run.py --run-id ui-global-align-20260507T054841Z` wrote `artifacts/runs/ui-global-align-20260507T054841Z/trace-run.json`.
- IP-centered follow-up: `cd ai-pic-frontend && npm run lint` passed with `0 errors, 19 warnings`; warnings match the existing StoryboardEditor hook-dependency warnings, existing `<img>` warnings, and eslint config default-export warning.
- IP-centered follow-up: `cd ai-pic-frontend && npm run test` passed: `7 passed`.
- IP-centered follow-up: `cd ai-pic-frontend && npm run build` passed.
- IP-centered follow-up: `python scripts/check_repo_docs.py` passed.
- IP-centered follow-up: `python scripts/check_repo_contracts.py --mode diff <changed files>` passed.
- IP-centered browser doctor passed: `python scripts/harness/doctor.py --run-id ui-ip-center-20260507T063324Z --nginx-url http://localhost:8089 --api-url http://localhost:8000 --frontend-url http://localhost:8089 --env-file docker/.env.lite`.
- IP-centered browser evidence stored under `artifacts/runs/ui-ip-center-20260507T063324Z/`.
- IP-centered browser scenarios passed with Playwright fallback after Chrome DevTools timed out at `http://127.0.0.1:9222`:
  - `workbench_smoke`
  - `story_master_detail_smoke`
  - `episode_timeline_smoke`
  - `episode_workspace_storyboard_smoke`
  - `virtual_ip_list_smoke`
  - `environment_migration_smoke`
- IP-centered trace passed: `python scripts/harness/trace_run.py --run-id ui-ip-center-20260507T063324Z` wrote `artifacts/runs/ui-ip-center-20260507T063324Z/trace-run.json`.
- IP/environment prototype validation passed: all 6 PNGs exist under `artifacts/ui-prototypes/2026-05-07-ip-environment-flow/` and use the intended gray-white operator tool direction.
- IP/environment closure: changed frontend TS/TSX files were checked for file size; none exceed the active repo diff contract after splitting `VirtualIPDetailPageParts`, `EnvironmentDetailState`, and `EnvironmentDetailViewParts`.
- IP/environment closure: `cd ai-pic-frontend && npm run lint` passed with `0 errors, 19 warnings`; warnings match the existing StoryboardEditor hook-dependency warnings, existing `<img>` warnings, and eslint config default-export warning.
- IP/environment closure: `cd ai-pic-frontend && npm run test` passed: `7 passed`.
- IP/environment closure: `cd ai-pic-frontend && npm run build` passed.
- IP/environment closure: `python scripts/check_repo_docs.py` passed.
- IP/environment closure: `python scripts/check_repo_contracts.py --mode diff <changed files>` passed after splitting the IP detail page below the repo file-size threshold.
- IP/environment browser doctor passed: `python scripts/harness/doctor.py --run-id ui-ip-env-align-20260507T092901Z --nginx-url http://localhost:8089 --api-url http://localhost:8000 --frontend-url http://localhost:8089 --env-file docker/.env.lite`.
- IP/environment browser evidence stored under `artifacts/runs/ui-ip-env-align-20260507T092901Z/`.
- IP/environment browser scenarios passed with Playwright fallback after Chrome DevTools timed out at `http://127.0.0.1:9222`:
  - `workbench_smoke`
  - `virtual_ip_list_smoke`
  - `virtual_ip_detail_smoke`
  - `virtual_ip_image_generation_smoke` (redirected through existing `/virtual-ip/[id]/images` semantics to `/virtual-ip/[id]`)
  - `environment_migration_smoke`
  - `environment_detail_smoke`
- IP/environment trace passed: `python scripts/harness/trace_run.py --run-id ui-ip-env-align-20260507T092901Z` wrote `artifacts/runs/ui-ip-env-align-20260507T092901Z/trace-run.json`.
- Pre-commit before commit was attempted with `pre-commit run --all-files` and failed on existing broad repository baseline noise outside this change:
  - `end-of-file-fixer` attempted to modify many old storyboard/agent_chats files; those hook-created unrelated changes were reverted before staging.
  - `ruff` reported existing violations in old migration/template/provider/storyboard files outside this change.
  - `backend-pytest` used the host Python 3.13 environment and failed during test bootstrap on an existing `ensure_scenes` import path issue; the scoped backend pytest commands above passed in the repo backend environment earlier.
  - Commit used the scoped passing gates plus this documented pre-commit baseline failure rather than including unrelated hook churn.

## Next Steps

- Later split the legacy Storyboard editor into smaller production components; V2 only constrains its outer support workspace.
- Consider adding a dedicated compact story synopsis field in backend data cleanup so the frontend no longer needs to normalize fenced JSON legacy values.
- Complete the data migration that connects IP and environment assets into story/episode records, then replace migration copy with real IP/environment readiness metrics.

## Linked Commits

- (pending)
