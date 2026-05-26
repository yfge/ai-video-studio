---
id: 2026-05-26T07-57-35Z-provider-chain-video-concurrency
date: "2026-05-26T07:57:35Z"
participants:
  - user
  - codex
models:
  - gpt-5-codex
tags:
  - provider-chain
  - harness
  - seedance
  - latency
related_paths:
  - scripts/harness/provider_chain_regression.py
  - scripts/harness/provider_chain_media.py
  - ai-pic-backend/tests/scripts/test_provider_chain_media.py
  - tasks.md
  - docs/exec-plans/active/main-chain-commercial-readiness.md
  - docs/exec-plans/active/timeline-main-chain.md
summary: Add concurrent video clip generation to the provider-chain harness.
---

## User Prompt

继续。

## Goals

- Reduce full-30s regression wall-clock time after the previous live run showed two serial 15 second Seedance calls taking about `402.957s` and `440.514s`.
- Keep the harness Timeline-first and preserve deterministic evidence ordering.
- Make provider latency observable in the provider-chain artifact.

## Changes

- Added `--video-concurrency` to `provider_chain_regression.py`, defaulting to `2`.
- Changed `generate_videos_for_timeline` to generate independent Timeline video clips concurrently when more than one clip is present.
- Each concurrent clip uses a cloned `requests.Session` with copied auth headers and cookies.
- Per-clip request evidence is merged back into `request_chain` in clip order.
- Added `key_artifacts.video_generation` with `clip_count`, `concurrency`, and `wall_time_seconds`.
- Added a focused unit test proving both clip requests enter the concurrent path and that request evidence remains ordered.

## Validation

- `python -m py_compile scripts/harness/provider_chain_regression.py scripts/harness/provider_chain_media.py` passed.
- `cd ai-pic-backend && PYTEST_ADDOPTS=--no-cov pytest tests/scripts/test_provider_chain_media.py tests/scripts/test_provider_chain_api.py tests/scripts/test_provider_chain_regression.py tests/scripts/test_provider_chain_render_probe.py -q` passed: `9 passed, 26 warnings`.
- A new live full-30s run was not repeated for this commit. The immediately preceding full-30s run already consumed two real Seedance 15 second generations and established the latency problem; this commit is covered by deterministic concurrency unit evidence plus existing live chain evidence.
- `python scripts/check_repo_docs.py` passed.
- `python scripts/check_repo_contracts.py --mode diff <changed files>` passed.
- `git diff --check` passed.
- `pre-commit run --files <changed files>` passed, including repository docs, contracts, ledger enforcement, and backend quick gate.

## Next Steps

- If full-30s remains too slow or flaky even with concurrency, move system video generation to an async task/polling API rather than holding a synchronous HTTP request open.
- Keep 4 second smoke as the normal live regression gate; keep full-30s as a low-frequency paid gate.

## Linked Commits

Pending
