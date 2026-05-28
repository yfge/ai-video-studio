---
id: "2026-05-28T11-43-09Z-text-generation-route-options"
date: "2026-05-28T11:43:09Z"
participants:
  - user
  - codex
models:
  - gpt-5
tags:
  - scripts
  - provider-chain
  - deepseek
  - api
  - quality-gate
related_paths:
  - ai-pic-backend/app/api/v1/ai_text_generation.py
  - ai-pic-backend/app/api/v1/api.py
  - ai-pic-backend/tests/unit/test_ai_text_generation_route.py
  - docs/exec-plans/active/commercial-script-quality.md
summary: Preserve public text-generation stream and thinking options for provider-backed script validation.
---

## User Prompt

commit

## Goals

- Continue moving generated scripts toward commercial short-drama quality.
- Fix the public `/api/v1/ai/generate/text` route so provider-chain script probes can actually disable streaming and thinking.
- Keep the fix out of oversized legacy `ai_providers.py`.

## Changes

- Added Task 44 and Task 45 to `docs/exec-plans/active/commercial-script-quality.md`.
- Added `ai_text_generation.py`, a focused text-generation route that accepts `stream` and `thinking` and forwards both options to `ai_service.ai_manager.generate_text`.
- Registered the focused text route before the legacy AI provider route in `api.py` so `/api/v1/ai/generate/text` resolves to the option-preserving endpoint.
- Added route-order and passthrough tests proving the request model accepts `stream`/`thinking` and the endpoint forwards them.

## Validation

- Red test:
  `cd ai-pic-backend && pytest tests/unit/test_ai_text_generation_route.py -q`
  failed as expected before the route fix: `assert 'stream' in fields` failed because the first registered `/ai/generate/text` route used the legacy request model without `stream` or `thinking`.
- Green targeted route test:
  `cd ai-pic-backend && pytest tests/unit/test_ai_text_generation_route.py -q`
  passed: 2 passed, 28 warnings.
- Temporary worktree backend:
  restarted `ai-video-backend-worktree-commercial` on `http://localhost:8010`; `curl -fsS http://localhost:8010/health` returned `{"status":"healthy","logging":"enabled"}`.
- Live text-generation probe:
  authenticated against `http://localhost:8010/api/v1/auth/login` as `geyunfei`, then posted to `/api/v1/ai/generate/text` with `model=deepseek-v4-flash`, `prefer_provider=deepseek`, `max_tokens=80`, `stream=false`, and `thinking=false`.
  Result: login 200 in 0.326s; text generation 200 in 1.858s with provider `deepseek`, model `deepseek-v4-flash`, and content `{"title":"测试","scenes":[]}`.
- Live log evidence:
  container logs for run id `text-probe-worktree-route-options-20260528Tlocal` showed request body carrying `"stream": false, "thinking": false` and `LLM Request ... params={'temperature': 0.1, 'json_schema': False, 'stream': False, 'max_tokens': 80}`.
- Browser/MCP note:
  This was a backend-only route fix for a provider-chain blocker. I used direct authenticated API reproduction against the temporary backend instead of Chrome DevTools because the decisive failure path was the `/api/v1/ai/generate/text` request body being dropped before the provider call. I did not claim browser verification for this slice.
- Focused validation:
  `cd ai-pic-backend && pytest tests/unit/test_ai_text_generation_route.py tests/unit/test_ai_providers_http_exception_passthrough.py tests/scripts/test_provider_chain_api.py -q`
  passed: 12 passed, 33 warnings.
- Full backend gate:
  `cd ai-pic-backend && pytest`
  failed after 1m27s: 2139 passed, 94 skipped, 3 failed, 2099 warnings. Failures were outside this route slice:
  `tests/integration/test_timeline_pipeline_import_api.py::test_process_timeline_pipeline_imports_audio_timeline_to_timeline_spec` failed because `timeline_pipeline` no longer exposes `TimelineShotPlanService` for the test monkeypatch;
  `tests/scripts/test_provider_chain_regression.py::test_extract_structured_script_requires_dialogue` failed because the fixture script lacks the current required scene fields (`question`, first missing);
  `tests/scripts/test_script_story_structure_sync.py::test_generate_script_syncs_normalized_scenes` failed on local MySQL access denied for `root@172.18.0.1`.
- Repo docs:
  `python scripts/check_repo_docs.py`
  passed: `[check_repo_docs] ok`.
- Repo contracts:
  `{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs python scripts/check_repo_contracts.py --mode diff`
  passed: `[check_repo_contracts] ok (diff)`.
- Whitespace:
  `git diff --check`
  passed with no output.
- Targeted pre-commit:
  `{ git diff --name-only main...HEAD; git diff --name-only; git ls-files --others --exclude-standard; } | sort -u | xargs env SKIP=backend-pytest pre-commit run --files`
  passed: merge-conflict, whitespace, yaml, ruff, black, isort, prettier, repo docs, repo contracts, and agent_chats ledger hooks passed; backend quick pytest was skipped for the documented local MySQL default issue; frontend lint had no files to check.

## Next Steps

- Re-run a full provider-chain smoke from the current worktree after this slice is committed when budget allows; this commit proves the text route no longer forces `stream=True`, but it does not by itself prove full image/video generation or commercial-quality sample-scale scripts.
- Full goal remains open until fresh provider/browser evidence shows generated scripts pass the commercial quality gates at sample scale.

## Linked Commits

- Current commit: `fix(scripts): forward text generation options`.
