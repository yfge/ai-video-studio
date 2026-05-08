---
id: 2026-05-07T13-49-38Z-unified-operator-ui
date: 2026-05-07T13:49:38Z
participants: [human, codex]
models: [gpt-5]
tags: [frontend, ui, operator, virtual-ip, environments, stories, episodes]
summary: "Unify IP-centered operator UI across the main production routes"
---

## User Prompt

PLEASE IMPLEMENT THIS PLAN: IP 中心统一 Operator UI 设计与落地计划. Generate unified image prototypes first, then deeply align the main operator UI across workbench, IP, environment, story, episode, and episode workspace routes without changing backend APIs, database schema, route semantics, generation flows, or npm dependencies.

## Goals

- Produce seven unified IP-centered operator UI reference PNGs.
- Make the main production routes share one operator shell, breadcrumb/context header, workspace grid, rail/main/inspector structure, tabs, toolbar, modal/drawer, button, status, and form language.
- Deeply reduce visible old styles in the episode script workspace and story episode generation panel while preserving existing hooks and generation behavior.
- Keep all touched TS/TSX files within the repo file-size contract.

## Changes

- Generated and self-checked seven PNG prototypes under `artifacts/ui-prototypes/2026-05-07-unified-operator-ui/`:
  - `01-ip-command-center.png`
  - `02-ip-asset-hub.png`
  - `03-environment-asset-workspace.png`
  - `04-story-production-board.png`
  - `05-episode-production-board.png`
  - `06-episode-timeline-workspace.png`
  - `07-generation-drawer-states.png`
- Added shared operator primitives for workspace layout, context rail, main canvas, inspector, toolbar, tabs, entity header, list row, modal frame, drawer, textarea, and class composition.
- Updated `OperatorShell` navigation to the IP-centered order and changed the top header to show breadcrumb plus page title/subtitle, preserving smoke-required page identity text.
- Aligned the workbench, IP list/detail, environment list/detail, story master-detail, story detail, and episode workspace routes around the same breadcrumb and operator workspace grammar.
- Tightened `OperatorWorkspace` to a bounded viewport-height work area so long story lists, IP detail content, and inspectors scroll internally instead of stretching the whole page.
- Moved IP image management into the IP detail main canvas so `/virtual-ip/[id]` remains a single fixed operator workspace with a stable right inspector.
- Converted the episode workspace page to use `OperatorShell`; tightened workflow steps, script selector, Timeline workspace, and script tab controls to the operator style.
- Split the oversized script tab into `useWorkspaceScriptStructure`, model helpers, and UI parts so the touched files remain under the hard file-size limit.
- Split story episode generation fields into `EpisodeGeneratePanelFields` and replaced old purple/green CTA styling with operator buttons and compact form controls.
- Updated `episode_script_generation_form_smoke` to assert the stable script workspace control text `重新生成剧本` instead of the old no-script-only form text.

## Validation

- Prototype validation passed: all seven PNGs exist at `artifacts/ui-prototypes/2026-05-07-unified-operator-ui/`; the generated API size is `1536x1024` for each PNG. `01-ip-command-center.png` was regenerated once because the first attempt cropped the left nav.
- File-size validation passed through the repo diff contract; notable touched files remain within limits, including `ScriptGenerationForm.tsx` at 250 lines and `EpisodeTimelineWorkspace.tsx` at 250 lines.
- `cd ai-pic-frontend && npm run lint` passed with `0 errors, 19 warnings`; warnings match the existing eslint config, StoryboardEditor hook warnings, and existing `<img>` warnings.
- `cd ai-pic-frontend && npm run test` passed: `7 passed`.
- `cd ai-pic-frontend && npm run build` passed.
- `git diff --check` passed.
- `python scripts/check_repo_docs.py` passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>` passed.
- Browser doctor passed: `python scripts/harness/doctor.py --run-id ui-unified-operator-20260507T213200Z --nginx-url http://localhost:8089 --api-url http://localhost:8000 --frontend-url http://localhost:8089 --env-file docker/.env.lite`.
- Browser evidence stored under `artifacts/runs/ui-unified-operator-20260507T213200Z/`.
- Browser scenarios passed with Playwright fallback after Chrome DevTools timed out at `http://127.0.0.1:9222`:
  - `workbench_smoke`
  - `virtual_ip_list_smoke`
  - `virtual_ip_detail_smoke`
  - `virtual_ip_image_generation_smoke`
  - `environment_migration_smoke`
  - `environment_detail_smoke`
  - `story_master_detail_smoke`
  - `episode_timeline_smoke`
  - `episode_workspace_storyboard_smoke`
  - `episode_script_generation_form_smoke`
- `python scripts/harness/trace_run.py --run-id ui-unified-operator-20260507T213200Z` passed and wrote `artifacts/runs/ui-unified-operator-20260507T213200Z/trace-run.json`.
- Screenshot acceptance after reruns: story list and IP detail no longer stretch the page into long screenshots; the main routes show the same left nav, breadcrumb/title header, bounded workspace, and inspector pattern at the 1365px desktop smoke viewport.

## Next Steps

- Continue reducing the legacy `StoryboardEditor.js` internal UI in a dedicated pass; this round keeps the large editor internals functionally intact.
- Later replace migration copy with real IP/environment linkage metrics once the asset migration is complete.

## Linked Commits

- This commit.
