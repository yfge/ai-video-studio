## User Prompt

PLEASE IMPLEMENT THIS PLAN: Timeline-First 内容质量验证计划。

## Goals

- Add a repeatable quality regression harness for timeline-first provider samples.
- Separate read-only audit of existing evidence from live 10-sample production runs.
- Gate script quality, timeline order, render structure, character lineage, and frame evidence.
- Keep the existing provider chain timeline-first path intact while allowing varied script premises.

## Changes

- Added `scripts/harness/production_quality_regression.py` as the CLI entrypoint.
- Added split helper modules for live sample execution, IO artifacts, script scoring, and quality gates.
- Added `--script-premise` to `provider_chain_regression.py` and the DeepSeek script prompt path.
- Added targeted tests for quality aggregation, character-lineage hard gates, retry-adjusted success, and premise injection.

## Validation

- `cd ai-pic-backend && pytest tests/scripts/test_production_quality_regression.py tests/scripts/test_provider_chain_regression.py tests/scripts/test_provider_chain_media.py -q`
  - Result: `12 passed, 26 warnings`.
- `python scripts/check_repo_docs.py`
  - Result: `[check_repo_docs] ok`.
- `python scripts/check_repo_contracts.py --mode diff scripts/harness/provider_chain_api.py scripts/harness/provider_chain_payloads.py scripts/harness/provider_chain_regression.py scripts/harness/production_quality_regression.py scripts/harness/production_quality_report.py scripts/harness/production_quality_script.py scripts/harness/production_quality_io.py scripts/harness/production_quality_gates.py scripts/harness/production_quality_live.py ai-pic-backend/tests/scripts/test_production_quality_regression.py`
  - Result: `[check_repo_contracts] ok (diff)`.
- `git diff --check`
  - Result: passed.
- `python scripts/harness/production_quality_regression.py --mode audit-existing --run-id quality-audit-20260527T034052Z --input-run timeline-first-full-30s-20260526T090328Z`
  - Result: report written to `artifacts/runs/quality-audit-20260527T034052Z/quality_report.json`.
  - Verdict: `not_trial_ready`; existing evidence proves timeline/render structure but not 10-sample stability or fresh 6-frame character consistency.

## Next Steps

- Run `live-10` against the local system API with external provider budget enabled.
- Inspect generated contact sheets before claiming character visual consistency.
- Run browser validation against the latest Timeline workspace and render/clip-asset requests after live samples finish.

## Linked Commits

Pending
