## User Prompt

PLEASE IMPLEMENT THIS PLAN: Provider-Backed Production Quality Proof Plan.

## Goals

- Prove the Timeline-first production chain with real providers after the
  Seedance quota/billing preflight.
- Stop paid sampling when provider billing/quota failures recur.
- Only change code when evidence shows missing failure classification or lost
  request evidence.
- Record the final state as one of `trial-ready`, `not-ready`, or
  `provider-blocked`.

## Changes

- Added raw DeepSeek script parse failure evidence to
  `scripts/harness/provider_chain_api.py` under
  `key_artifacts.script_generation_error`.
- Added transport-error request-chain records for response-less API failures.
- Tightened provider-chain failure classification in
  `scripts/harness/provider_chain_regression.py`:
  - `JSONDecodeError` script extraction failures now classify as
    `script_generation_failed`.
  - `ConnectionError`, `RemoteDisconnected`, `ReadTimeout`, and
    `ConnectTimeout` request failures now classify as `api_transport_failed`.
  - classification evidence now includes request-chain `error` fields.
- Added regression tests in:
  - `ai-pic-backend/tests/scripts/test_provider_chain_api.py`
  - `ai-pic-backend/tests/scripts/test_provider_chain_failures.py`
- Updated provider-backed proof status in:
  - `docs/cartoon-sample-production-proof.md`
  - `tasks.md`

## Validation

- Seedance billing preflight:
  `artifacts/runs/seedance-billing-preflight-20260527T143214Z/provider_chain.json`
  returned `ok=true`, render job `34`, final URL
  `https://resource.lets-gpt.com/timeline-renders/video/20260527/143758/21f4648f.mp4`,
  and `render_media_probe.ok=true`.
- Three-sample paid precheck:
  `artifacts/runs/quality-live-3-20260527T143829Z/quality_report.json`
  had `provider_billing_or_quota_error_count=0`; provider/render evidence was
  present on final sample attempts, but the aggregate remained
  `chain_ready_quality_not_proven`.
- First formal live-10 attempt
  `artifacts/runs/quality-live-10-20260527T152641Z/` exposed an unclassified
  DeepSeek JSON parse failure; the run was interrupted and classification was
  fixed before continuing.
- Second formal live-10 attempt
  `artifacts/runs/quality-live-10-20260527T155552Z/` exposed a response-less
  API transport failure; the run was interrupted and request evidence plus
  classification were fixed before continuing.
- Final formal live-10 attempt:
  `artifacts/runs/quality-live-10-20260527T155906Z/quality_report.json`
  reached `provider_blocked_not_evaluable` after `sample-03` received
  Volcengine `AccountOverdueError` on `POST /api/v1/ai/generate/video`.
  The run was stopped to avoid further paid samples. Aggregate at stop:
  `sample_count=3`, `first_success_count=1`,
  `retry_adjusted_success_count=1`,
  `provider_billing_or_quota_error_count=1`,
  `script_lint_average=9.83`, and `structured_script_average=3.81`.
- Browser evidence:
  `python scripts/harness/browser_flow.py --scenario episode_timeline_smoke --run-id quality-live-10-20260527T155906Z-browser --base-url http://localhost:8089 --username geyunfei --password 'Gyf@845261' --episode-id 133 --script-id 117`
  returned `{"ok": true, "engine": "playwright"}`. Chrome DevTools timed out
  on `127.0.0.1:9222`, so this is Playwright fallback evidence, not Chrome
  verification. Summary:
  `artifacts/runs/quality-live-10-20260527T155906Z-browser/summary.json`.
- `pytest ai-pic-backend/tests/scripts/test_provider_chain_api.py ai-pic-backend/tests/scripts/test_provider_chain_failures.py ai-pic-backend/tests/scripts/test_provider_chain_regression.py ai-pic-backend/tests/scripts/test_provider_chain_media.py ai-pic-backend/tests/scripts/test_production_quality_regression.py ai-pic-backend/tests/test_timeline_shot_plan_api.py -q`
  passed: `27 passed, 50 warnings`.
- `python scripts/check_repo_docs.py` passed.
- `python scripts/check_repo_contracts.py --mode diff scripts/harness/provider_chain_api.py scripts/harness/provider_chain_regression.py ai-pic-backend/tests/scripts/test_provider_chain_api.py ai-pic-backend/tests/scripts/test_provider_chain_failures.py docs/cartoon-sample-production-proof.md tasks.md agent_chats/2026/05/27/2026-05-27T16-43-25Z-provider-backed-quality-proof.md`
  passed.
- `git diff --check` passed.

## Next Steps

- Clear the external Volcengine account overdue state.
- Restart from the Seedance smoke preflight before any new live-3 or live-10
  spend.
- Treat the current commercial readiness conclusion as `provider-blocked`, not
  `trial-ready`.

## Linked Commits

- None yet.
