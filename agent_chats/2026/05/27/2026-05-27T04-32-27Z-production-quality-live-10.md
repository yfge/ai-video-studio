## User Prompt

验证剧本质量、角色一致性、长期生产稳定性、以及真实项目内容是否足够好。

## Goals

- Run the new Timeline-first production quality harness with 10 provider-backed 30s cartoon samples.
- Preserve request chain, model/provider evidence, frame evidence, and browser validation evidence.
- Report the result honestly instead of treating a single generated video as production readiness.

## Changes

- No runtime code changes in this commit.
- Recorded the completed live-10 validation result and browser fallback evidence.

## Validation

- `python scripts/harness/production_quality_regression.py --mode live-10 --run-id quality-live-10-20260527T035257Z --api-url http://localhost:8000 --episode-id 133 --script-id 117 --sample-count 10 --duration-plan 15,15 --video-concurrency 2`
  - Result: completed.
  - Quality report: `artifacts/runs/quality-live-10-20260527T035257Z/quality_report.json`.
  - Verdict: `not_trial_ready`.
  - First-pass success: `0/10`.
  - Retry-adjusted success: `0/10`.
  - Script lint average: `7.34`, below the `9.0` threshold.
  - Structured script average: `3.35`, below the `3.5` threshold.
  - Failure categories across attempts: mostly `seedance_generation_failed`; one full-chain success still failed script lint.
- Successful full-chain evidence from sample 01 attempt 01:
  - Final render URL: `https://resource.lets-gpt.com/timeline-renders/video/20260527/040152/28de815b.mp4`.
  - Contact sheet: `artifacts/runs/quality-live-10-20260527T035257Z/frames/sample-01-attempt-1-contact-sheet.jpg`.
  - Visual review note: cartoon character stays non-real and roughly consistent in the only successful sample, but this does not offset the 0/10 production pass rate.
- Chrome DevTools MCP validation:
  - Result: unavailable; DevTools endpoint returned `127.0.0.1:9222/json/version HTTP Not Found`.
- Playwright fallback with system Chrome:
  - Result: passed.
  - Artifact: `artifacts/runs/quality-live-10-20260527T035257Z/browser/browser_validation.json`.
  - Verified login 200, Timeline render-jobs 200, and clip-assets 200.

## Next Steps

- Treat current state as not ready for trial operations.
- Fix Seedance 400 failure diagnostics and prompt/provider compatibility before rerunning live-10.
- Tighten script generation against `script_quality` before spending more video budget.
- Add automated categorization for Seedance 400 response bodies; current parallel generation path can lose the failed request body when a worker raises.

## Linked Commits

Pending
