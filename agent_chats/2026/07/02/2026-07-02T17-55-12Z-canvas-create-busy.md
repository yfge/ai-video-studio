---
id: 2026-07-02T17-55-12Z-canvas-create-busy
date: "2026-07-02T17:55:12Z"
participants:
  - user
  - codex
models:
  - GPT-5 Codex
tags:
  - ai-video-studio
  - production-canvas
  - delivery
related_paths:
  - ai-pic-frontend/src/components/features/canvas
  - ai-pic-frontend/tests
summary: Records one increment of the production infinite canvas implementation and its validation.
---

# Canvas Whole-Create Busy State

## User Prompt

继续完善无限画布功能。User also approved running `dev_in_docker` and validating with the built-in browser.

## Goals

- Make the whole-canvas creation button expose a machine-readable busy state.
- Ensure fast Docker/mock responses still leave a paint opportunity for the busy state.
- Validate the behavior with component tests and the real Docker browser path.

## Changes

- Added `aria-busy` to the `ProductionCanvasChatBar` whole-canvas create button while `running` is true.
- Added a one-frame yield before `createPlan` dispatch in `useProductionCanvasSkillPlanner`, so `执行中` can be painted even when `/production-canvas/plan` and auto-execute responses are very fast.
- Added tests for the chat bar busy attribute and for the planner ordering: button enters `执行中` before the plan request is sent.
- Wrote browser evidence to `artifacts/runs/2026-07-02T17-55-12Z-canvas-create-busy/in-app-browser-result.json`.

## Validation

1. Local checks:

- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasPlanner.test.tsx` -> red before implementation: new test failed with `1 !== 0`, proving the plan request was dispatched before a stable busy paint opportunity.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasPlanner.test.tsx` -> pass after implementation: 4 tests passed.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH node node_modules/.bin/tsx --test tests/productionCanvasChatBar.test.tsx` -> pass before full validation: 2 tests passed.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run test` -> pass: 176 tests, 32 suites.
- `cd ai-pic-frontend && PATH=/Users/geyunfei/.nvm/versions/node/v20.19.5/bin:$PATH npm run lint` -> pass with 0 errors and 3 existing warnings.
- `python scripts/check_repo_docs.py` -> pass.
- `python scripts/check_repo_contracts.py --mode audit` -> pass.
- `python scripts/check_repo_contracts.py --mode diff ...` scoped to the changed canvas files, tests, ledger, and browser artifact -> pass.

2. Browser or MCP validation:

- Entry URL: `http://localhost:8089/canvas`, served by the `docker/dev_in_docker.sh` stack through `ai-video-nginx`.
- User path: opened `/canvas`, used the existing logged-in test session, filled `生产目标` with `Codex 第四次验证整体创建忙碌态：并发采样`, filled `剧集 ID` with `1`, clicked `整体创建`, and sampled the button DOM concurrently.
- Console: no browser warnings or errors were reported for the validation tab.
- Network/backend: backend logs showed `POST /api/v1/production-canvas/plan` 200 for request `req-1783014892036-it3hivsd`, three `POST /api/v1/production-canvas/execute` 200 responses for `brief.compose`, `script.generate`, and `report.summarize`, and `PUT /api/v1/production-canvas/runs/0aa85e985fa740038f0e2c67317ed70b/state` 200.
- Result: at 10ms after click, the button rendered `执行中`, `aria-busy=true`, and `disabled=true`; the run completed with button text restored to `整体创建`, no alert, and run ID `0aa85e985fa740038f0e2c67317ed70b`.

3. Conflict signals and corrections:

- Initial assumption: adding `aria-busy` to the button was enough.
- Contradicting evidence: Docker browser sampling showed the mock backend returned so quickly that the UI could dispatch and complete the run before a stable busy state sample was visible.
- Reproduction and fix: added a failing planner test that expected no plan request before the busy paint opportunity, then inserted a one-frame yield before `createPlan`.
- Final verified state: the same Docker browser path captured the intended busy DOM state and completed the run successfully.

## Next Steps

- Continue tightening canvas interaction semantics incrementally.
- Keep `dev_in_docker` running for follow-up browser checks unless the user asks to stop it.

## Linked Commits

- Not committed.
