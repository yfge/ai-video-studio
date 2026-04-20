---
id: 2026-04-17T09-07-05Z-harness-foundation-phase1
date: 2026-04-17T09:07:05Z
participants: [human, codex]
models: [gpt-5]
tags: [harness, docs, reliability, ci]
related_paths:
  - AGENTS.md
  - FRONTEND.md
  - QUALITY_SCORE.md
  - README.md
  - RELIABILITY.md
  - .pre-commit-config.yaml
  - .github/workflows/ci-harness.yml
  - .github/workflows/nightly-harness.yml
  - ai-pic-frontend/package.json
  - ai-pic-frontend/package-lock.json
  - docker/README.md
  - docs/README.md
  - docs/architecture/contracts.md
  - docs/architecture/file-size-limits.md
  - docs/architecture/testing-policy.md
  - docs/architecture/agent-workflow.md
  - scripts/check_repo_docs.py
  - scripts/check_repo_contracts.py
  - scripts/contract_audit_core.py
  - scripts/contract_audit_reporting.py
  - scripts/harness/browser_flow.py
  - scripts/harness/browser_driver.js
  - scripts/harness/run_golden_path.py
  - scripts/harness/scenarios.py
  - scripts/harness/observability.py
  - scripts/harness/query_logs.py
  - scripts/harness/query_metrics.py
  - scripts/harness/trace_run.py
  - scripts/harness/trace_task.py
  - scripts/harness/score_quality.py
summary: "Implemented the Phase 1 harness foundation: light AGENTS entrypoint, contract audit reports, browser evidence contract, quality scoring, and nightly wiring."
---

## User Prompt

PLEASE IMPLEMENT THIS PLAN:

- shrink `AGENTS.md` into a lightweight entrypoint
- add architecture policy docs
- upgrade repo contracts from diff-only checks to audit plus diff blocking
- make browser evidence a formal harness contract
- generate quality scores from artifacts
- extend harness support toward golden paths and observability queries

## Goals

- Move repository process knowledge out of a monolithic `AGENTS.md` into structured docs.
- Produce machine-readable contract audit output under `artifacts/repo_audit/latest/`.
- Upgrade harness scripts so browser evidence, traces, and quality scoring follow a stable contract.
- Wire the new commands into pre-commit, README, and GitHub workflows.
- Validate the changes with repo checks plus a real local harness run when feasible.

## Changes

- Replaced the oversized `AGENTS.md` with a lightweight entrypoint that points at repository source-of-truth docs.
- Added `docs/architecture/contracts.md`, `docs/architecture/file-size-limits.md`, `docs/architecture/testing-policy.md`, and `docs/architecture/agent-workflow.md`, then indexed them in `docs/README.md`.
- Refactored `scripts/check_repo_docs.py` so docs drift can be reused programmatically.
- Split repository contract logic into `scripts/contract_audit_core.py` and `scripts/contract_audit_reporting.py`, and rebuilt `scripts/check_repo_contracts.py` as a thin CLI with `--mode diff|audit`, JSON output, and Markdown summaries.
- Added browser harness support files: `scripts/harness/browser_driver.js` plus the upgraded `browser_flow.py` artifact contract with `browser_flow.json`, `console.json`, `network.json`, `dom_snapshot.json`, and `screenshot.png`.
- Added harness observability helpers: `scripts/harness/observability.py`, `query_logs.py`, and `query_metrics.py`.
- Reworked `run_golden_path.py` and `scenarios.py` to emit contract-versioned scenario outputs and added `auth_login_and_me`, `task_traceability`, `virtual_ip_image_generation_real_or_mock`, `episode_timeline_generation`, and `timeline_export_end_to_end`.
- Updated `trace_run.py` and `trace_task.py` to include metrics and DOM snapshot evidence.
- Added `scripts/harness/score_quality.py` and regenerated `QUALITY_SCORE.md` from the current audit plus run artifacts.
- Updated `.pre-commit-config.yaml`, README files, and both harness workflows to use the new audit, trace, and scoring steps.
- Added `@playwright/test` to `ai-pic-frontend` devDependencies so the browser harness has a declared Playwright dependency.

## Validation

1. Local checks:

- `python -m py_compile scripts/check_repo_docs.py scripts/check_repo_contracts.py scripts/contract_audit_core.py scripts/contract_audit_reporting.py scripts/harness/browser_flow.py scripts/harness/run_golden_path.py scripts/harness/observability.py scripts/harness/query_logs.py scripts/harness/query_metrics.py scripts/harness/trace_run.py scripts/harness/trace_task.py scripts/harness/score_quality.py scripts/harness/scenarios.py` -> pass
- `node --check scripts/harness/browser_driver.js` -> pass
- `python scripts/check_repo_docs.py` -> pass
- `python scripts/check_repo_contracts.py --mode audit` -> pass and wrote `artifacts/repo_audit/latest/contracts-report.json` plus `contracts-summary.md`
- `python scripts/check_repo_contracts.py --mode diff ...` for the touched repo files -> pass
- `cd ai-pic-frontend && npm run lint` -> pass with 6 pre-existing warnings and 0 errors

2. Browser or MCP validation:

- Entry URL: `http://localhost:9229/login`
- User path: `python scripts/harness/doctor.py --run-id harness-foundation-check --nginx-url http://localhost:9229 --api-url http://localhost:8229 --frontend-url http://localhost:3229` followed by `python scripts/harness/browser_flow.py --scenario login_smoke --run-id harness-foundation-check --base-url http://localhost:9229`
- Console: browser harness recorded no page console events because no engine successfully reached the page
- Network: browser harness recorded no page network events because no engine successfully reached the page
- Result: `doctor.py` passed, but browser execution failed on all three engines and still produced the new artifact contract at `artifacts/runs/harness-foundation-check/`

3. Conflict signals and corrections:

- Initial assumption: the existing browser harness failures were mostly caused by the missing Playwright dependency
- Contradicting evidence: after adding `@playwright/test`, `browser_flow.py` still failed locally because Chrome DevTools timed out on `127.0.0.1:9222`, Playwright browser launch aborted with local macOS permission errors, and Selenium could not create a Chrome session
- Reproduction and fix: added the declared Playwright dependency, rewired module resolution to `ai-pic-frontend/package.json`, and reran the local browser harness to capture the real environment-specific failure artifacts instead of the earlier `MODULE_NOT_FOUND`
- Final verified state: browser artifact contract generation works, but this local desktop environment still blocks real browser execution; the failure is now explicit and recorded instead of being hidden behind missing dependencies

- `python scripts/harness/run_golden_path.py --scenario mock_smoke --run-id harness-foundation-check --base-url http://localhost:9229 --api-url http://localhost:8229` -> pass
- `python scripts/harness/run_golden_path.py --scenario auth_login_and_me --run-id harness-foundation-check --base-url http://localhost:9229 --api-url http://localhost:8229 --username geyunfei --password Gyf@845261` -> fail with `401 Unauthorized`, recorded in `artifacts/runs/harness-foundation-check/golden_path.json`
- `python scripts/harness/trace_run.py --run-id harness-foundation-check` -> pass
- `python scripts/harness/score_quality.py --run-id harness-foundation-check --write-quality-score` -> pass and regenerated `QUALITY_SCORE.md`
- `python scripts/harness/query_logs.py --run-id harness-foundation-check --limit 5` -> pass, returned zero matching records in the current local log stream
- `python scripts/harness/query_metrics.py --run-id harness-foundation-check` -> pass, returned an empty metric summary because the current local log file did not contain that `run_id`

## Next Steps

- Fix local Chrome/Playwright execution permissions so `browser_flow.py` can achieve a real Chrome-backed pass instead of a recorded failure.
- Verify whether the documented local test account is still valid for the current lite harness stack, because the current `auth_login_and_me` scenario returns `401`.
- Expand nightly golden paths beyond auth and task traceability once the required fixture IDs and credentials are stable.
- Start Phase 2 hotspot reduction using the new audit report as the debt backlog instead of manual inspection.

## Linked Commits

- Planned subject: `chore(harness): land phase1 foundation`
