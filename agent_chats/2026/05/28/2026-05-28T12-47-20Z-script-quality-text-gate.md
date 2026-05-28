## User Prompt

commit

## Goals

- Commit the current script-quality slice without claiming the broader commercial-quality goal is complete.
- Add a text-only 10-sample harness that can measure generated-script stability before image, audio, video, or render cost.
- Preserve the live 10-sample result, including the fact that the current generator still does not prove commercial script quality.

## Changes

- Added `scripts/harness/production_script_quality_regression.py`.
- Added `ai-pic-backend/tests/scripts/test_production_script_quality_regression.py`.
- Updated `docs/exec-plans/active/commercial-script-quality.md` with Tasks 51-52.

## Validation

- Red test:
  - `cd ai-pic-backend && pytest tests/scripts/test_production_script_quality_regression.py -q`
  - Failed before implementation with `ModuleNotFoundError: No module named 'scripts.harness.production_script_quality_regression'`.
- Green focused test:
  - `cd ai-pic-backend && pytest tests/scripts/test_production_script_quality_regression.py -q`
  - Passed: `4 passed, 26 warnings`.
- Contract check during implementation:
  - `{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs python scripts/check_repo_contracts.py --mode diff`
  - Passed: `[check_repo_contracts] ok (diff)`.
- Live text-only evidence:
  - `python scripts/harness/production_script_quality_regression.py --run-id script-quality-live-text-10-20260528Tlocal --api-url http://localhost:8010 --sample-count 10 --timeout-seconds 900`
  - Evidence: `artifacts/runs/script-quality-live-text-10-20260528Tlocal/script_quality_report.json`.
  - Verdict: `script_quality_not_proven`.
  - Aggregate: 10/10 samples, provider billing/quota errors 0, script lint average 9.85, structured script average 3.68, script score average 3.55.
  - Failure shape: first-pass success 0/10 and retry-adjusted success 0/10, with the blocker in external script score and generation/preflight stability.
- Final focused validation:
  - `cd ai-pic-backend && pytest tests/scripts/test_production_script_quality_regression.py tests/scripts/test_provider_chain_api.py tests/scripts/test_production_quality_regression.py -q`
  - Passed: `26 passed, 27 warnings`.
- Repository checks:
  - `python scripts/check_repo_docs.py`: `[check_repo_docs] ok`.
  - `{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs python scripts/check_repo_contracts.py --mode diff`: `[check_repo_contracts] ok (diff)`.
  - `git diff --check`: passed with no output.
  - `{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs env SKIP=backend-pytest pre-commit run --files`: passed all enabled hooks; `pytest (backend quick gate)` was skipped because focused pytest covered this harness slice.

## Next Steps

- Improve the DeepSeek prompt/preflight path so the script score reaches >= 4.0 while preserving the current lint and structured-score gains.
- Rerun the text-only 10-sample harness before spending full media/render cost.
- The broader commercial-quality goal remains open until stable text evidence and later full-chain visual evidence pass.

## Linked Commits

- Pending commit for this slice.
