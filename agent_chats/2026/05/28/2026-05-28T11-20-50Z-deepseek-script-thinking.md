---
id: "2026-05-28T11-20-50Z-deepseek-script-thinking"
date: "2026-05-28T11:20:50Z"
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - scripts
  - provider-chain
  - deepseek
  - quality-gate
related_paths:
  - ai-pic-backend/app/services/providers/deepseek_request.py
  - ai-pic-backend/tests/unit/test_deepseek_provider_v4.py
  - scripts/harness/provider_chain_api.py
  - scripts/harness/production_quality_api_checks.py
  - docs/exec-plans/active/commercial-script-quality.md
summary: Disable DeepSeek streaming and thinking for script-quality verification paths.
---

## User Prompt

Continue working toward the active thread goal: 让剧本达到商用水准

## Goals

- Move from deterministic local gates toward real provider-backed quality evidence.
- Fix the request shape that blocked live script-quality smoke validation before it reached image/video generation.
- Make provider-chain script generation and quality probes avoid the slow DeepSeek V4 thinking path for JSON/script-quality verification.

## Changes

- Added Task 42 and Task 43 to `docs/exec-plans/active/commercial-script-quality.md`.
- Updated `deepseek_request.py` so `deepseek-v4-flash` defaults to `thinking={"type":"disabled"}`, while explicit thinking and V4 Pro thinking behavior remain available.
- Updated `scripts/harness/provider_chain_api.py` so DeepSeek script JSON generation sends `stream=False` and `thinking=False` hints for runtimes that expose those options.
- Updated `scripts/harness/production_quality_api_checks.py` so live lint checks send `stream=False` and `thinking=False` hints.
- Added/extended tests for DeepSeek V4 Flash request defaults and provider-chain script request shape.

## Validation

- Local API health:
  `curl -sS -m 5 http://localhost:8000/health`
  returned `{"status":"healthy","logging":"enabled"}`.
- Existing sample audit with current gates:
  `python scripts/harness/production_quality_regression.py --mode audit-existing --run-id quality-audit-current-gates-20260528Tlocal --input-run /Users/geyunfei/dev/yfge/ai-video-studio/artifacts/runs/quality-live-10-20260527T155906Z-sample-01-attempt-1/provider_chain.json`
  returned verdict `not_trial_ready`; the old sample passed Timeline/render checks but failed newer script gates (`scene_min_beats`, `payoff_required`, `scene_conflict_question`, `scene_conflict_stakes`, `scene_conflict_opposition`, `scene_conflict_turn`, `scene_protagonist_screen_presence`) and script lint average was 8.5.
- Live smoke attempt:
  `python scripts/harness/provider_chain_regression.py --mode smoke --run-id quality-smoke-current-prompt-20260528Tlocal --api-url http://localhost:8000 --episode-id 133 --script-id 117 --timeout-seconds 900 --poll-interval-seconds 5 --video-concurrency 1`
  failed after the client-side 900 second timeout. Artifact: `artifacts/runs/quality-smoke-current-prompt-20260528Tlocal/provider_chain.json`. It reached login and model availability (`text_generation`, `text_to_image`, `text_to_video`, `image_to_video` all 200), then failed at `deepseek-script` with `ReadTimeout: HTTPConnectionPool(host='localhost', port=8000): Read timed out. (read timeout=900)`. Failure category: `api_transport_failed`.
- Minimal text probe:
  direct `/api/v1/ai/generate/text` call with `max_tokens=80` returned login 200 in 0.248s, then `ReadTimeout` after 45.005s.
- Scoring probe:
  direct `/api/v1/scoring/score` call returned login 200, then `ReadTimeout` after 60.003s.
- Red tests:
  `cd ai-pic-backend && pytest tests/unit/test_deepseek_provider_v4.py::test_build_chat_request_defaults_v4_flash_to_non_thinking tests/unit/test_deepseek_provider_v4.py::test_generate_text_defaults_to_v4_flash_non_stream tests/scripts/test_provider_chain_api.py::test_generate_script_disables_deepseek_streaming_and_thinking -q`
  failed as expected: the two DeepSeek request-builder assertions failed on missing `thinking`, while the provider-chain request-shape test already proved the harness body carried `stream=False` and `thinking=False`.
- Green targeted tests:
  `cd ai-pic-backend && pytest tests/unit/test_deepseek_provider_v4.py::test_build_chat_request_defaults_v4_flash_to_non_thinking tests/unit/test_deepseek_provider_v4.py::test_generate_text_defaults_to_v4_flash_non_stream tests/scripts/test_provider_chain_api.py::test_generate_script_disables_deepseek_streaming_and_thinking -q`
  passed: 3 passed, 28 warnings.
- Focused validation:
  `cd ai-pic-backend && pytest tests/unit/test_deepseek_provider_v4.py tests/scripts/test_provider_chain_api.py tests/scripts/test_provider_chain_payloads.py tests/scripts/test_production_quality_regression.py -q`
  passed: 31 passed, 30 warnings.
- Repo docs:
  `python scripts/check_repo_docs.py`
  passed: `[check_repo_docs] ok`.
- Repo contracts:
  `{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs python scripts/check_repo_contracts.py --mode diff`
  passed after moving the fix out of oversized legacy files: `[check_repo_contracts] ok (diff)`.
- Whitespace:
  `git diff --check`
  passed with no output.
- Targeted pre-commit:
  `{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs env SKIP=backend-pytest pre-commit run --files`
  passed: merge-conflict, whitespace, yaml, ruff, black, isort, prettier, repo docs, repo contracts, and agent_chats ledger hooks passed; backend quick pytest was skipped for the documented local MySQL default issue; frontend lint had no files to check.

## Next Steps

- Re-run the provider-chain smoke after the local API service is restarted onto this branch or after this patch is merged into the running backend image; the current Docker service still runs the old DeepSeek request builder.
- Full goal remains open until fresh provider/browser evidence shows generated scripts pass the commercial quality gates at sample scale.

## Linked Commits

- Current commit: `fix(scripts): disable thinking for quality probes`.
