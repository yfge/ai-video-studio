## User Prompt

继续 Timeline-First 内容质量验证，并确保剧本质量、角色一致性、长期生产稳定性用真实系统 API 回归。

## Goals

- Fix the quality harness so `script_quality` lint actually runs from the repository root.
- Avoid treating skipped script lint as a valid live-10 quality run.

## Changes

- Changed `production_quality_script.py` to insert `ai-pic-backend` at the front of `sys.path`.
- This prevents an installed third-party `app` package from shadowing the repository backend package.
- Stopped the incomplete `quality-live-10-20260527T034141Z` run after discovering lint was skipped; attempt-1 evidence remains under artifacts for diagnosis.

## Validation

- `python - <<'PY' ... from scripts.harness.production_quality_script import ScriptLintOptions, lint_script_content ... PY`
  - Result: both imports are available from repo root.
- `cd ai-pic-backend && pytest tests/scripts/test_production_quality_regression.py -q`
  - Result: `5 passed, 26 warnings`.
- `python scripts/check_repo_contracts.py --mode diff scripts/harness/production_quality_script.py`
  - Result: `[check_repo_contracts] ok (diff)`.
- `python scripts/check_repo_docs.py`
  - Result: `[check_repo_docs] ok`.
- `git diff --check`
  - Result: passed.

## Next Steps

- Re-run `live-10` from scratch so script lint, DeepSeek ScriptScore, frame extraction, and provider-chain gates all participate.
- Record browser validation after the live run completes.

## Linked Commits

Pending
