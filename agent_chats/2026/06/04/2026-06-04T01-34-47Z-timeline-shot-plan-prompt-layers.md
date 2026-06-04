## User Prompt

PLEASE IMPLEMENT THIS PLAN: Timeline-First 分镜提示词五层优化

## Goals

- Encode the article-derived five-layer prompt method into Timeline-native shot plans.
- Keep Timeline as the single source of truth and keep Storyboard/Grid Storyboard as support views.
- Add `live_action` shot-plan style support and surface prompt-layer editing in the operator workspace.

## Changes

- Extended `timeline_shot_plan` generation schema with direction, aesthetic reference, geometry, motion timeline, emotional landing, and prompt method fields.
- Added `live_action` support to Timeline shot-plan requests while preserving existing `2d_cartoon` and `3d_cartoon` styles.
- Propagated prompt layers into storyboard support frames and grid-storyboard panel/video prompts with fallback for older shot plans.
- Added frontend parsing, Timeline spec patching, prompt-layer display/editing, and grid storyboard style selection.
- Added `updateTimeline` frontend API helper for the existing `PATCH /api/v1/timelines/{timeline_id}` endpoint; the editor patches only prompt-layer source refs and clears stale grid support data.
- Documented the prompt bundle as Timeline clip support data, not a new Storyboard orchestration source.

## Validation

- `cd ai-pic-backend && pytest tests/test_timeline_shot_plan_api.py tests/test_timeline_shot_plan_prompt_layers.py tests/unit/services/audio/test_storyboard_from_timeline_spec.py tests/unit/services/storyboard/test_grid_storyboard_prompt_bridge.py -v` -> passed, 13 tests.
- `cd ai-pic-frontend && npm run lint` -> passed with 18 existing warnings in unrelated files/config.
- `cd ai-pic-frontend && npm run test` -> passed, 35 tests.
- `python scripts/check_repo_docs.py` -> passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>` -> passed.
- `cd ai-pic-backend && python -u run_tests.py quick` -> failed before tests started while installing dependencies. Pip reported a Python 3.13 dependency conflict: `pydantic==2.5.0` conflicts with `langchain-core==0.2.43`, which requires `pydantic>=2.7.4` for `python_full_version >= "3.12.4"`.
- Browser evidence:
  - `python scripts/harness/browser_flow.py --scenario episode_workspace_storyboard_smoke --run-id 20260604T015620Z-timeline-prompt-layers-episode86 --username geyunfei --password 'Gyf@845261' --episode-id 86` -> passed with `selected_engine=playwright` and `selected_status=degraded`; Chrome DevTools CDP timed out first.
  - Standalone Playwright probes on episode 86 / timeline 64 confirmed prompt-layer editor availability, `PATCH /api/v1/timelines/64` returned 200 for prompt-layer save, style select changed from `live_action` to `3d_cartoon`, and `POST /api/v1/timelines/64/storyboard-grid/generate` returned 200 with task `6020`.
  - Evidence JSON: `artifacts/runs/20260604T015620Z-timeline-prompt-layers-ui/prompt-layer-ui.json`.
  - Material console/network errors: none after filtering dev-only HMR websocket 404s and aborted chunk/workbench requests.

## Next Steps

- Resolve the repository-wide backend quick dependency conflict separately if `run_tests.py quick` must run on Python 3.13.

## Linked Commits

- None yet.
